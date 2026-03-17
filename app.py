import os
import json
import logging
import faiss
import numpy as np
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Skill Match Hub", description="AI-Powered Job Matching Platform")

# Paths to data
DATA_DIR = "data"
RESUME_INDEX_PATH = os.path.join(DATA_DIR, "resume_faiss.index")
RESUME_METADATA_PATH = os.path.join(DATA_DIR, "resume_metadata.json")
JOB_INDEX_PATH = os.path.join(DATA_DIR, "rag_vector_index.faiss")
JOB_METADATA_PATH = os.path.join(DATA_DIR, "job_description_chunks_metadata.json")

# Global variables for models and data
embedding_model = None
resume_index = None
resume_metadata = []
job_index = None
job_metadata = []
groq_client = None

# Models
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

class SearchResult(BaseModel):
    id: str
    score: float
    content: str
    metadata: Dict[str, Any]
    llm_analysis: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    global embedding_model, resume_index, resume_metadata, job_index, job_metadata, groq_client
    
    logger.info("Loading embedding model...")
    # Use the same model as in vectorization scripts
    embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    logger.info("Loading FAISS indices and metadata...")
    
    # Load Resume Data (for Recruiter Search)
    if os.path.exists(RESUME_INDEX_PATH) and os.path.exists(RESUME_METADATA_PATH):
        resume_index = faiss.read_index(RESUME_INDEX_PATH)
        with open(RESUME_METADATA_PATH, 'r', encoding='utf-8') as f:
            resume_metadata = json.load(f)
        logger.info(f"Loaded resume index with {resume_index.ntotal} vectors")
    else:
        logger.warning(f"Resume index or metadata not found at {RESUME_INDEX_PATH} / {RESUME_METADATA_PATH}")

    # Load Job Data (for Seeker Search)
    if os.path.exists(JOB_INDEX_PATH) and os.path.exists(JOB_METADATA_PATH):
        job_index = faiss.read_index(JOB_INDEX_PATH)
        with open(JOB_METADATA_PATH, 'r', encoding='utf-8') as f:
            job_metadata = json.load(f)
        logger.info(f"Loaded job index with {job_index.ntotal} vectors")
    else:
        logger.warning(f"Job index or metadata not found at {JOB_INDEX_PATH} / {JOB_METADATA_PATH}")

    # Initialize Groq Client
    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        groq_client = Groq(api_key=api_key)
        logger.info("Groq client initialized")
    else:
        logger.warning("GROQ_API_KEY not found in environment variables. LLM features will be disabled.")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "resume_index_loaded": resume_index is not None,
        "job_index_loaded": job_index is not None,
        "groq_client_loaded": groq_client is not None
    }

def get_embedding(text: str) -> np.ndarray:
    # Normalize embeddings to match training (L2 norm)
    embedding = embedding_model.encode(text, normalize_embeddings=True)
    return np.array([embedding]).astype("float32")

def generate_llm_analysis(prompt: str) -> str:
    if not groq_client:
        return "AI Analysis currently offline (System check required)."
    
    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert HR AI assistant. Be concise, professional, and highlight key matches and gaps."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=500,
        )
        return completion.choices[0].message.content
    except Exception as e:
        # Check specifically for 401/Invalid Key
        err_msg = str(e)
        if "401" in err_msg or "api_key" in err_msg.lower():
            logger.error(f"Groq API key invalid: {e}")
            return "AI Analysis currently offline (System maintenance)."
        logger.error(f"Groq API error: {e}")
        return "AI Analysis currently offline (System busy)."

@app.post("/api/recruiter/search", response_model=List[SearchResult])
async def recruiter_search(request: SearchRequest):
    """
    Recruiter pastes a JD -> Search Resumes
    """
    if not resume_index:
        raise HTTPException(status_code=503, detail="Resume index not loaded")

    # 1. Embed query (JD)
    query_vector = get_embedding(request.query)

    # 2. Search FAISS
    scores, indices = resume_index.search(query_vector, request.top_k)
    
    results = []
    candidates_context = []

    for score, idx in zip(scores[0], indices[0]):
        if idx == -1: continue # invalid index
        
        meta = resume_metadata[idx]
        candidate_text = meta.get("text", "")
        # Fallback for name if missing in deeper metadata
        candidate_name = meta.get("metadata", {}).get("name", "Unknown Candidate")
        
        results.append(SearchResult(
            id=str(idx),
            score=float(score),
            content=candidate_text[:500] + "...", # Truncate for display
            metadata=meta.get("metadata", {}),
            llm_analysis=None # Will fill later
        ))
        
        candidates_context.append(f"Candidate: {candidate_name}\nScore: {score:.2f}\nProfile: {candidate_text}\n---")

    # 3. LLM Evaluation (Batch or per-item? Let's do a quick summary for the top result or per-item short analysis)
    # For a better UX, let's analyze the top match specifically or provide a comparative summary.
    # The requirement implies "evaluation on top results". Let's do a quick analysis for each of the top 3.
    
    if groq_client:
        for i, res in enumerate(results[:3]):
            prompt = f"""
            Job Description: "{request.query[:1000]}"
            Candidate Profile: "{candidates_context[i]}"

            Provide a professional evaluation in exactly this format:
            MATCHED SKILLS: [list 3-5 key skills found in both]
            MISSING SKILLS: [list 2-3 key requirements missing]
            SUMMARY: [2 sentences why they fit]
            """
            res.llm_analysis = generate_llm_analysis(prompt)

    return results

@app.post("/api/seeker/search", response_model=List[SearchResult])
async def seeker_search(request: SearchRequest):
    """
    Job Seeker pastes Resume -> Search Jobs
    """
    if not job_index:
        raise HTTPException(status_code=503, detail="Job index not loaded")

    # 1. Embed query (Resume)
    query_vector = get_embedding(request.query)

    # 2. Search FAISS
    scores, indices = job_index.search(query_vector, request.top_k)
    
    results = []
    jobs_context = []

    for score, idx in zip(scores[0], indices[0]):
        if idx == -1: continue
        
        meta = job_metadata[idx]
        job_text = meta.get("text", "")
        job_title = meta.get("metadata", {}).get("job_title", "Unknown Role")
        company = meta.get("metadata", {}).get("company", "Unknown Company")

        results.append(SearchResult(
            id=str(idx),
            score=float(score),
            content=job_text[:500] + "...",
            metadata=meta.get("metadata", {}),
            llm_analysis=None
        ))
        
        jobs_context.append(f"Job: {job_title} at {company}\nScore: {score:.2f}\nDescription: {job_text}\n---")

    # 3. LLM Advice
    if groq_client:
        for i, res in enumerate(results[:3]):
            prompt = f"""
            Candidate Resume: "{request.query[:1000]}"
            Job Posting: "{jobs_context[i]}"

            Provide a professional evaluation in exactly this format:
            MATCHED SKILLS: [list 3-5 key skills you have]
            SKILLS GAP: [list 2-3 things to learn to get this job]
            ADVICE: [2 sentences on how to stand out]
            """
            res.llm_analysis = generate_llm_analysis(prompt)

    return results

# Serve static files (Frontend)
# We mount this last so API routes take precedence
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
