import os
import re
import json
import faiss
import torch
import pdfplumber
from tkinter import Tk, filedialog
from transformers import AutoTokenizer, AutoModel

HF_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 20
FAISS_INDEX_FILE = "resume_faiss.index"
METADATA_FILE = "resume_metadata.json"
MAX_TOKENS = 256

index = faiss.read_index(FAISS_INDEX_FILE)

with open(METADATA_FILE, "r", encoding="utf-8") as f:
    metadata_store = json.load(f)

print(f" FAISS loaded: {index.ntotal} vectors")
print(f" Metadata loaded: {len(metadata_store)} entries")


device = "cuda" if torch.cuda.is_available() else "cpu"
print(f" Using device: {device}")

tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_NAME)
model = AutoModel.from_pretrained(HF_MODEL_NAME).to(device)
model.eval()

def clean_text(text):
    return " ".join(text.split()).replace("\x00", "").lower()


def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return clean_text(text)


def extract_experience_from_jd(text):
    match = re.search(r"(\d+(\.\d+)?)\s*\+?\s*years", text)
    return float(match.group(1)) if match else 0.0


def extract_skills_from_jd(text):
    stop_words = {
        "experience", "years", "knowledge", "required", "skills",
        "ability", "good", "strong", "hands", "working"
    }
    words = set(re.findall(r"[a-zA-Z]{3,}", text))
    return {w for w in words if w not in stop_words}


def embed_text(text):
    encoded = tokenizer(
        text,
        truncation=True,
        padding=True,
        max_length=MAX_TOKENS,
        return_tensors="pt"
    ).to(device)

    with torch.no_grad():
        output = model(**encoded)
        token_embeddings = output.last_hidden_state
        mask = encoded["attention_mask"].unsqueeze(-1).float()

        pooled = (token_embeddings * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
        pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)

    return pooled.cpu().numpy().astype("float32")


def upload_pdf(title):
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    path = filedialog.askopenfilename(
        title=title,
        filetypes=[("PDF files", "*.pdf")]
    )

    root.destroy()
    return path


def search_faiss(vector, top_k=TOP_K):
    distances, indices = index.search(vector, top_k)

    candidates = []

    for idx, dist in zip(indices[0], distances[0]):
        if idx >= len(metadata_store):
            continue

        entry = metadata_store[idx]
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
            "file_path": entry.get("file_path", "Unknown")
        })

    return candidates


def match_and_rank(candidates, jd_skills, jd_experience):
    final_results = []

    for c in candidates:
        resume_exp = c["experience_years"]

        if jd_experience > 0 and resume_exp < jd_experience:
            continue

        resume_skills = [s.lower() for s in c["skills"]]

        matched_skills = [
            s for s in resume_skills
            if any(jd in s for jd in jd_skills)
        ]

        if not matched_skills:
            continue

        skill_score = len(matched_skills) / max(len(resume_skills), 1)

        final_score = (
            0.7 * c["semantic_score"] +
            0.3 * skill_score
        )

        c["matched_skills"] = matched_skills
        c["final_score"] = round(final_score, 4)

        final_results.append(c)

    return sorted(final_results, key=lambda x: x["final_score"], reverse=True)


def find_best_employees():
    print("\n Upload Job Description PDF")
    jd_path = upload_pdf("Select Job Description PDF")

    if not jd_path:
        print("No JD selected")
        return []

    print(f"JD uploaded: {os.path.basename(jd_path)}")

    jd_text = extract_text_from_pdf(jd_path)

    jd_experience = extract_experience_from_jd(jd_text)
    jd_skills = extract_skills_from_jd(jd_text)

    print(f"JD Experience Required: {jd_experience} years")
    print(f"JD Skills Extracted: {len(jd_skills)} skills")

    jd_vector = embed_text(jd_text)

    candidates = search_faiss(jd_vector)
    print(f"✓ Found {len(candidates)} initial candidates")

    return match_and_rank(candidates, jd_skills, jd_experience)


if __name__ == "__main__":
    employees = find_best_employees()

    if not employees:
        print("\n No suitable candidates found")
    else:
        print("\n" + "=" * 60)
        print("         TOP MATCHED EMPLOYEES")
        print("=" * 60 + "\n")

        for rank, emp in enumerate(employees[:5], 1):
            print(f"RANK {rank}")
            print("-" * 60)
            print(f"Name                    : {emp['name']}")
            print(f"Email                   : {emp['email']}")
            print(f"Internship Years        : {emp['internship_years']}")
            print(f"Experience Years        : {emp['experience_years']}")
            print(f"Total Experience Years  : {emp['total_experience_years']}")
            print(f"Matched Skills          : {emp['matched_skills']}")
            print(f"Resume File             : {emp['filename']}")
            print(f"Resume Path             : {emp['file_path']}")
            print()

