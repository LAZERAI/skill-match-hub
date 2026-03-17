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

# Force reload environment
load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Skill Match Hub")

# Paths
DATA_DIR = "data"
RESUME_INDEX_PATH = os.path.join(DATA_DIR, "resume_faiss.index")
RESUME_METADATA_PATH = os.path.join(DATA_DIR, "resume_metadata.json")
JOB_INDEX_PATH = os.path.join(DATA_DIR, "rag_vector_index.faiss")
JOB_METADATA_PATH = os.path.join(DATA_DIR, "job_description_chunks_metadata.json")

# Globals
embedding_model = None
resume_index = None
resume_metadata = []
job_index = None
job_metadata = []
groq_client = None

@app.on_event("startup")
async def startup_event():
    global embedding_model, resume_index, resume_metadata, job_index, job_metadata, groq_client
    
    logger.info("Starting up Skill Match Hub...")
    embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    if os.path.exists(RESUME_INDEX_PATH):
        resume_index = faiss.read_index(RESUME_INDEX_PATH)
        with open(RESUME_METADATA_PATH, 'r', encoding='utf-8') as f:
            resume_metadata = json.load(f)
            
    if os.path.exists(JOB_INDEX_PATH):
        job_index = faiss.read_index(JOB_INDEX_PATH)
        with open(JOB_METADATA_PATH, 'r', encoding='utf-8') as f:
            job_metadata = json.load(f)

    # Key handling
    api_key = os.getenv("GROQ_API_KEY")
    if api_key and api_key.startswith("gsk_"):
        groq_client = Groq(api_key=api_key)
        logger.info("Groq client initialized with valid key format.")
    else:
        logger.error("GROQ_API_KEY missing or invalid format in environment.")

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

class SearchResult(BaseModel):
    id: str
    score: float
    content: str
    metadata: Dict[str, Any]
    llm_analysis: Optional[str] = None

def get_embedding(text: str) -> np.ndarray:
    embedding = embedding_model.encode(text, normalize_embeddings=True)
    return np.array([embedding]).astype("float32")

def generate_llm_analysis(prompt: str) -> str:
    if not groq_client:
        return "SERVICE_OFFLINE: Groq API client not initialized. Check server environment variables."
    
    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a senior recruiter. Provide analysis in 3 short bullet points. Do not mention errors or internal IDs."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=300,
        )
        return completion.choices[0].message.content
    except Exception as e:
        err = str(e)
        if "401" in err: return "AUTH_ERROR: Invalid API key provided to Groq."
        if "429" in err: return "RATE_LIMIT: Groq API quota exceeded."
        return f"ANALYSIS_ERROR: {err}"

@app.post("/api/recruiter/search", response_model=List[SearchResult])
async def recruiter_search(request: SearchRequest):
    if not resume_index: raise HTTPException(status_code=503, detail="Index not ready")
    query_vector = get_embedding(request.query)
    scores, indices = resume_index.search(query_vector, request.top_k)
    
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1: continue
        meta = resume_metadata[idx]
        res = SearchResult(
            id=str(idx),
            score=float(score),
            content=meta.get("text", "")[:400] + "...",
            metadata=meta.get("metadata", {})
        )
        
        if groq_client and len(results) < 3:
            prompt = f"JD: {request.query[:500]}\nCandidate: {meta.get('text', '')[:1000]}\nAnalyze fit."
            res.llm_analysis = generate_llm_analysis(prompt)
        
        results.append(res)
    return results

@app.post("/api/seeker/search", response_model=List[SearchResult])
async def seeker_search(request: SearchRequest):
    if not job_index: raise HTTPException(status_code=503, detail="Index not ready")
    query_vector = get_embedding(request.query)
    scores, indices = job_index.search(query_vector, request.top_k)
    
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1: continue
        meta = job_metadata[idx]
        res = SearchResult(
            id=str(idx),
            score=float(score),
            content=meta.get("text", "")[:400] + "...",
            metadata=meta.get("metadata", {})
        )
        
        if groq_client and len(results) < 3:
            prompt = f"Resume: {request.query[:500]}\nJob: {meta.get('text', '')[:1000]}\nProvide career advice."
            res.llm_analysis = generate_llm_analysis(prompt)
            
        results.append(res)
    return results

@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "groq_ready": groq_client is not None,
        "resume_index_size": len(resume_metadata),
        "job_index_size": len(job_metadata)
    }

app.mount("/", StaticFiles(directory="static", html=True), name="static")
