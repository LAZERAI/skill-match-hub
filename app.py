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
        return "OFFLINE // CLIENT_NOT_READY"
    
    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a technical recruiter. Provide analysis in a strict KEY: VALUE format. Keys: SKILLS_SCORE, EXP_SCORE, EDU_SCORE, MISSING, SUMMARY."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=400,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"ERROR // {str(e)}"

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
            prompt = f"""
            JD: {request.query[:500]}
            Candidate Profile: {meta.get('text', '')[:1000]}
            
            Evaluate and return ONLY this format:
            SKILLS_SCORE: [0-100]
            EXP_SCORE: [0-100]
            EDU_SCORE: [0-100]
            MISSING: [list 2 items]
            SUMMARY: [1 short sentence]
            """
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
            prompt = f"""
            Resume: {request.query[:500]}
            Job: {meta.get('text', '')[:1000]}
            
            Evaluate and return ONLY this format:
            SKILLS_SCORE: [0-100]
            EXP_SCORE: [0-100]
            EDU_SCORE: [0-100]
            MISSING: [list 2 items to learn]
            SUMMARY: [1 short advice sentence]
            """
            res.llm_analysis = generate_llm_analysis(prompt)
            
        results.append(res)
    return results

app.mount("/", StaticFiles(directory="static", html=True), name="static")
