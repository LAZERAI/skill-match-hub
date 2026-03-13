from fastapi import FastAPI
from app.models.query_model import QueryRequest
from app.services.search import search_resumes
from app.services.llm_service import rank_candidates

app = FastAPI()


@app.get("/")
def home():
    return {"message": "AI Recruitment API Running"}


@app.post("/llm/query")
def query_llm(request: QueryRequest):

    query = request.query

    results = search_resumes(query)

    ranked_results = rank_candidates(results)

    return {
        "query": query,
        "results": ranked_results
    }