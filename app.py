"""
Skill Match Hub — FastAPI Backend
Consolidates HR + Seeker matching pipelines into a single web-ready API.
"""
import os
import re
import json
import time
import asyncio
import faiss
import torch
import numpy as np
import pdfplumber
import io
from pathlib import Path
from groq import Groq
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModel
from dotenv import load_dotenv

# ── Load .env ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ── Config ────────────────────────────────────────────────────────────────────
# Source data (kept in the repository)
REPO_DATA_DIR = BASE_DIR / "full_code"

# Persistent storage (Hugging Face Spaces uses /mnt/data for persistent storage)
PERSISTENT_DIR = Path(os.getenv("PERSISTENT_DIR", "/mnt/data/skill-match-hub"))
PERSISTENT_DIR.mkdir(parents=True, exist_ok=True)

RESUME_META_PATH = REPO_DATA_DIR / "resume_metadata.json"
JOB_CHUNKS_PATH = REPO_DATA_DIR / "job_description_chunks.json"

# Faiss indexes must be saved/loaded using file paths (str) for the faiss write_index/read_index bindings.
RESUME_FAISS_PATH = str(PERSISTENT_DIR / "resume_faiss.index")
JOB_FAISS_PATH = str(PERSISTENT_DIR / "rag_vector_index.faiss")
JOB_META_PATH = str(PERSISTENT_DIR / "job_description_chunks_metadata.json")

# Embedding / LLM config
HF_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "llama-3.3-70b-versatile"
TOP_K_RECRUITER = 20
TOP_K_SEEKER = 5
MAX_TOKENS = 256

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(title="Skill Match Hub")

# ── Global state ──────────────────────────────────────────────────────────────
resume_index = None
resume_metadata = []
job_index = None
job_metadata = []
tokenizer = None
embed_model = None
groq_client = None
device = "cpu"

# Building state (used for progress / UX feedback)
building_resume_index = False
building_job_index = False
building_indexes = False


# ── Request / Response models ─────────────────────────────────────────────────
class RecruiterRequest(BaseModel):
    job_description: str


class SeekerRequest(BaseModel):
    resume_text: str


# ── Helpers ───────────────────────────────────────────────────────────────────
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output.last_hidden_state
    mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * mask_expanded, dim=1) / torch.clamp(
        mask_expanded.sum(dim=1), min=1e-9
    )


def embed_text(text: str) -> np.ndarray:
    encoded = tokenizer(
        text, truncation=True, padding=True,
        max_length=MAX_TOKENS, return_tensors="pt"
    ).to(device)

    with torch.no_grad():
        output = embed_model(**encoded)
        embedding = mean_pooling(output, encoded["attention_mask"])

    vec = embedding.squeeze().cpu().numpy().astype("float32")
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.reshape(1, -1)


def clean_text(text: str) -> str:
    return " ".join(text.split()).replace("\x00", "").lower()


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF file bytes."""
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text.strip()


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extract text from TXT file bytes."""
    # Try UTF-8 first, fall back to latin-1
    try:
        return file_bytes.decode("utf-8").strip()
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1").strip()


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Extract text from PDF or TXT file."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in ("txt", "text"):
        return extract_text_from_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: .{ext}. Please upload a PDF or TXT file.")


def extract_experience_from_jd(text: str) -> float:
    match = re.search(r"(\d+(\.\d+)?)\s*\+?\s*years", text, re.IGNORECASE)
    return float(match.group(1)) if match else 0.0


def extract_skills_from_jd(text: str) -> set:
    stop_words = {
        "experience", "years", "knowledge", "required", "skills",
        "ability", "good", "strong", "hands", "working"
    }
    words = set(re.findall(r"[a-zA-Z]{3,}", text.lower()))
    return words - stop_words


# ── Recruiter pipeline ────────────────────────────────────────────────────────
def search_resume_faiss(vector, top_k=TOP_K_RECRUITER):
    distances, indices = resume_index.search(vector, top_k)
    candidates = []
    for idx, dist in zip(indices[0], distances[0]):
        if idx >= len(resume_metadata):
            continue
        entry = resume_metadata[idx]
        meta = entry.get("metadata", {})
        candidates.append({
            "semantic_score": float(dist),
            "name": meta.get("name", "Unknown"),
            "email": meta.get("email", "Unknown"),
            "skills": meta.get("skills", []),
            "experience_years": meta.get("experience_years", 0.0),
            "internship_years": meta.get("internship_years", 0.0),
            "total_experience_years": meta.get("total_experience_years", 0.0),
            "filename": entry.get("filename", "Unknown"),
        })
    return candidates


def match_and_rank(candidates, jd_skills, jd_experience):
    results = []
    for c in candidates:
        if jd_experience > 0 and c["experience_years"] < jd_experience:
            continue

        resume_skills = [s.lower() for s in c["skills"]]
        matched = [s for s in resume_skills if any(jd in s for jd in jd_skills)]

        if not matched:
            continue

        skill_score = len(matched) / max(len(resume_skills), 1)
        final_score = 0.7 * c["semantic_score"] + 0.3 * skill_score
        c["matched_skills"] = matched
        c["final_score"] = round(final_score, 4)
        results.append(c)

    return sorted(results, key=lambda x: x["final_score"], reverse=True)


def hr_evaluation(candidate: dict) -> str:
    prompt = f"""You are an HR evaluator.

Candidate Information (trusted):
Name: {candidate.get("name")}
Email: {candidate.get("email")}
Experience Years: {candidate.get("experience_years")}
Internship Years: {candidate.get("internship_years")}
Total Experience: {candidate.get("total_experience_years")}
Skills: {", ".join(candidate.get("skills", []))}
Matched Skills: {", ".join(candidate.get("matched_skills", []))}

Evaluate ONLY:
1. Candidate Summary
2. Strengths
3. Skill Gaps
4. Hiring Recommendation (Hire / Consider / Reject)

Do NOT hallucinate."""

    try:
        response = groq_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a strict HR analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM evaluation unavailable: {str(e)}"


# ── Seeker pipeline ───────────────────────────────────────────────────────────
def search_job_faiss(vector, top_k=TOP_K_SEEKER):
    scores, indices = job_index.search(vector, top_k)
    results = []
    for idx, score in zip(indices[0], scores[0]):
        if idx >= len(job_metadata):
            continue
        entry = job_metadata[idx]
        results.append({
            "similarity_score": float(score),
            "text": entry.get("text", ""),
            "metadata": entry.get("metadata", {})
        })
    return results


def seeker_analysis(job_match: dict) -> str:
    md = job_match.get("metadata", {})
    company = md.get("company", "Not provided")
    role = md.get("job_title", "Not provided")
    location = md.get("location", "Not provided")

    prompt = f"""You are a career advisor.

Company Name: {company}
Job Role: {role}
Location: {location}

Job Description (supporting context only):
{job_match.get("text", "")[:1000]}

Based on the job details above, provide:
1. A brief role summary
2. Key requirements
3. Why this could be a good match
4. Tips to strengthen application

Be concise and helpful."""

    try:
        response = groq_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful career advisor."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM analysis unavailable: {str(e)}"


# ── Core search logic (shared by text and file endpoints) ─────────────────────
def run_recruiter_search(jd_text: str) -> dict:
    if resume_index is None:
        raise HTTPException(status_code=503, detail="Resume index not loaded.")
    if not jd_text:
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")

    t0 = time.time()

    jd_clean = clean_text(jd_text)
    jd_experience = extract_experience_from_jd(jd_clean)
    jd_skills = extract_skills_from_jd(jd_clean)
    jd_vector = embed_text(jd_clean)

    candidates = search_resume_faiss(jd_vector)
    ranked = match_and_rank(candidates, jd_skills, jd_experience)

    results = []
    for cand in ranked[:6]:
        evaluation = hr_evaluation(cand)
        cand["llm_evaluation"] = evaluation
        results.append(cand)

    elapsed = round(time.time() - t0, 2)
    print(f"[Recruiter] {len(results)} candidates matched in {elapsed}s")

    return {
        "candidates": results,
        "total_found": len(ranked),
        "elapsed_seconds": elapsed
    }


def run_seeker_search(resume_text: str) -> dict:
    if job_index is None:
        raise HTTPException(status_code=503, detail="Job index not loaded.")
    if not resume_text:
        raise HTTPException(status_code=400, detail="Resume text cannot be empty.")

    t0 = time.time()

    resume_vector = embed_text(resume_text)
    matches = search_job_faiss(resume_vector)

    results = []
    for match in matches[:5]:
        analysis = seeker_analysis(match)
        md = match.get("metadata", {})
        results.append({
            "similarity_score": match["similarity_score"],
            "job_title": md.get("job_title", "Unknown"),
            "company": md.get("company", "Unknown"),
            "location": md.get("location", "Unknown"),
            "description_preview": match["text"][:300],
            "llm_analysis": analysis
        })

    elapsed = round(time.time() - t0, 2)
    print(f"[Seeker] {len(results)} jobs matched in {elapsed}s")

    return {
        "jobs": results,
        "elapsed_seconds": elapsed
    }


def _update_building_state():
    """Internal: keep the combined building flag in sync."""
    global building_indexes
    building_indexes = building_resume_index or building_job_index


def build_resume_index():
    """Build or load the index used for recruiter searches."""
    global resume_index, resume_metadata, building_resume_index
    building_resume_index = True
    _update_building_state()

    try:
        # Load existing index if available
        if os.path.exists(RESUME_FAISS_PATH) and os.path.exists(RESUME_META_PATH):
            print("Loading resume FAISS index...")
            resume_index = faiss.read_index(RESUME_FAISS_PATH)
            with open(RESUME_META_PATH, "r", encoding="utf-8") as f:
                resume_metadata = json.load(f)
            print(f"Resume index: {resume_index.ntotal} vectors, {len(resume_metadata)} entries")
            return

        # Otherwise build from metadata JSON
        if os.path.exists(RESUME_META_PATH):
            print("Building resume FAISS index from metadata JSON...")
            with open(RESUME_META_PATH, "r", encoding="utf-8") as f:
                resume_metadata = json.load(f)

            vectors = []
            for entry in resume_metadata:
                text = entry.get("text", "")
                if not text:
                    continue
                vectors.append(embed_text(text).squeeze().astype("float32"))

            if vectors:
                arr = np.vstack(vectors)
                faiss.normalize_L2(arr)
                idx = faiss.IndexFlatIP(arr.shape[1])
                idx.add(arr)
                resume_index = idx
                faiss.write_index(resume_index, RESUME_FAISS_PATH)
                print(f"Built resume index: {resume_index.ntotal} vectors")
            else:
                print("WARNING: Resume metadata contains no text to vectorize.")
        else:
            print("WARNING: Resume metadata JSON not found. Recruiter search unavailable.")
    finally:
        building_resume_index = False
        _update_building_state()


def build_job_index():
    """Build or load the index used for seeker searches."""
    global job_index, job_metadata, building_job_index
    building_job_index = True
    _update_building_state()

    try:
        # Load existing (persisted) index if available
        if os.path.exists(JOB_FAISS_PATH) and os.path.exists(JOB_META_PATH):
            print("Loading job FAISS index...")
            job_index = faiss.read_index(JOB_FAISS_PATH)
            with open(JOB_META_PATH, "r", encoding="utf-8") as f:
                job_metadata = json.load(f)
            print(f"Job index: {job_index.ntotal} vectors, {len(job_metadata)} entries")
            return

        # Otherwise build from job chunks stored in the repository
        if JOB_CHUNKS_PATH.exists():
            print("Building job FAISS index from job description chunks...")
            with open(JOB_CHUNKS_PATH, "r", encoding="utf-8") as f:
                chunks = json.load(f)

            vectors = []
            for chunk in chunks:
                text = chunk.get("text", "")
                if not text:
                    continue
                vectors.append(embed_text(text).squeeze().astype("float32"))

            if vectors:
                arr = np.vstack(vectors)
                faiss.normalize_L2(arr)
                idx = faiss.IndexFlatIP(arr.shape[1])
                idx.add(arr)
                job_index = idx
                faiss.write_index(job_index, JOB_FAISS_PATH)
                with open(JOB_META_PATH, "w", encoding="utf-8") as f:
                    json.dump(chunks, f, indent=2, ensure_ascii=False)
                job_metadata = chunks
                print(f"Built job index: {job_index.ntotal} vectors")
            else:
                print("WARNING: Job chunks JSON contains no text to vectorize.")
        else:
            print("WARNING: Job chunks JSON not found. Job seeker search unavailable.")
    finally:
        building_job_index = False
        _update_building_state()


def build_faiss_indexes():
    """Build FAISS indexes from JSON data sources (if index files aren't present)."""
    build_resume_index()
    build_job_index()


# ── Runtime state ───────────────────────────────────────────────────────────
building_indexes = False


async def build_faiss_indexes_async():
    """Run the blocking FAISS build process in a background thread."""
    global building_indexes
    building_indexes = True
    try:
        await asyncio.to_thread(build_faiss_indexes)
    finally:
        building_indexes = False


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    global tokenizer, embed_model, groq_client, device

    # Groq client
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("WARNING: GROQ_API_KEY not set. LLM calls will fail.")
    groq_client = Groq(api_key=api_key or "")

    # Device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # Embedding model
    print("Loading embedding model...")
    tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_NAME)
    embed_model = AutoModel.from_pretrained(HF_MODEL_NAME).to(device)
    embed_model.eval()
    print("Embedding model ready.")

    # Build indexes in background (allows the server to start fast)
    asyncio.create_task(build_faiss_indexes_async())


# ── API routes: TEXT input ────────────────────────────────────────────────────
@app.post("/api/recruiter/search")
async def recruiter_search(req: RecruiterRequest):
    return run_recruiter_search(req.job_description.strip())


@app.post("/api/seeker/search")
async def seeker_search(req: SeekerRequest):
    return run_seeker_search(req.resume_text.strip())


# ── API routes: FILE upload (PDF / TXT) ───────────────────────────────────────
@app.post("/api/recruiter/upload")
async def recruiter_upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File too large (max 10MB).")

    try:
        text = extract_text_from_file(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read file. Please check the file format.")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from the file.")

    return run_recruiter_search(text)


@app.post("/api/seeker/upload")
async def seeker_upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File too large (max 10MB).")

    try:
        text = extract_text_from_file(file_bytes, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read file. Please check the file format.")

    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from the file.")

    return run_seeker_search(text)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "resume_index_loaded": resume_index is not None,
        "resume_count": len(resume_metadata),
        "job_index_loaded": job_index is not None,
        "job_count": len(job_metadata),
        "building_resume_index": building_resume_index,
        "building_job_index": building_job_index,
        "building_indexes": building_indexes,
    }


@app.post("/api/rebuild-index")
async def rebuild_index():
    """Trigger a background rebuild of FAISS indexes.

    Returns quickly while the rebuild continues in the background.
    """
    if building_indexes:
        return {
            "status": "ok",
            "message": "Index rebuild already in progress.",
            "resume_index_loaded": resume_index is not None,
            "job_index_loaded": job_index is not None,
        }

    asyncio.create_task(build_faiss_indexes_async())
    return {
        "status": "ok",
        "message": "Index rebuild started.",
        "resume_index_loaded": resume_index is not None,
        "job_index_loaded": job_index is not None,
    }


# ── Serve frontend ───────────────────────────────────────────────────────────
STATIC_DIR = str(BASE_DIR / "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))
