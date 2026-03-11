import faiss
import json
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

index = faiss.read_index("resume_faiss.index")

with open("resume_metadata.json", "r") as f:
    metadata = json.load(f)


def search_vectors(query, top_k=5):

    query_embedding = model.encode([query])

    D, I = index.search(query_embedding, top_k)

    results = []

    for idx in I[0]:
        results.append(metadata[idx])

    return results