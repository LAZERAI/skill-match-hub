import os
import json
import torch
import faiss
import numpy as np
from transformers import AutoTokenizer, AutoModel

VALIDATED_JSON = "step4_validated.json"
FAISS_INDEX_PATH = "resume_faiss.index"
VECTOR_SIZE = 384
HF_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 250
CHUNK_OVERLAP = 50


device = "cuda" if torch.cuda.is_available() else "cpu"
tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_NAME)
model = AutoModel.from_pretrained(HF_MODEL_NAME).to(device)
model.eval()

def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output.last_hidden_state
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, dim=1) / torch.clamp(
        input_mask_expanded.sum(dim=1), min=1e-9
    )

def embed_text(text):
    encoded = tokenizer(text, truncation=True, padding=True, max_length=256, return_tensors="pt").to(device)

    with torch.no_grad():
        output = model(**encoded)

    embedding = mean_pooling(output, encoded["attention_mask"])
    vector = embedding.squeeze().cpu().numpy().astype("float32")

    norm = np.linalg.norm(vector)
    return (vector / norm if norm > 0 else vector).reshape(1, -1)


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    tokens = text.split()
    chunks = []

    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk = " ".join(tokens[start:end])
        chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def build_faiss_index():

    if not os.path.exists(VALIDATED_JSON):
        print(f"Error: {VALIDATED_JSON} not found!")
        return

    with open(VALIDATED_JSON, "r", encoding="utf-8") as f:
        resumes = json.load(f)

    vectors = []
    metadata_store = []

    print(f"Processing {len(resumes)} resumes")

    for i, r in enumerate(resumes):

        skills_text = ", ".join(r.get("skills", []))
        exp_text = f"{r.get('experience_years', 0.0)} years experience"
        intern_text = f"{r.get('internship_years', 0.0)} years internship"

        combined_text = f"""
        Candidate with skills: {skills_text}.
        Total experience: {exp_text}.
        Internship experience: {intern_text}.
        """

        combined_text = combined_text.strip()

        chunks = chunk_text(combined_text)

        for chunk in chunks:

            vec = embed_text(chunk)

            vectors.append(vec)

            metadata_store.append({

                "resume_id": r.get("resume_id"),
                "filename": r.get("filename"),
                "file_path": r.get("file_path"),
                "text": chunk,

                "metadata": {
                    "name": r.get("name", "Unknown"),
                    "email": r.get("email", "Unknown"),
                    "skills": r.get("skills", []),
                    "experience_years": r.get("experience_years", 0.0),
                    "internship_years": r.get("internship_years", 0.0),
                    "total_experience_years": r.get("total_experience_years", 0.0)
                }
            })

        if (i + 1) % 10 == 0 or (i + 1) == len(resumes):
            print(f"Processed {i+1}/{len(resumes)} resumes")

    vectors = np.vstack(vectors).astype("float32")

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    faiss.write_index(index, FAISS_INDEX_PATH)

    print(f"\nFAISS index saved: {FAISS_INDEX_PATH}")

    with open("resume_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata_store, f, indent=2, ensure_ascii=False)

    print("Metadata saved: resume_metadata.json")


if __name__ == "__main__":
    build_faiss_index()

