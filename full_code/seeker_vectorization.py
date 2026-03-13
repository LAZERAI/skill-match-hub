import json
import numpy as np
import faiss
import torch
from transformers import AutoTokenizer, AutoModel

PDF_JSON_FILE = "job_description_chunks.json"
FAISS_INDEX_FILE = "rag_vector_index.faiss"
METADATA_FILE = "job_description_chunks_metadata.json"
HF_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


with open(PDF_JSON_FILE, "r", encoding="utf-8") as f:
    pdf_chunks = json.load(f)

print(f"Total chunks loaded: {len(pdf_chunks)}")

tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_NAME)
model = AutoModel.from_pretrained(HF_MODEL_NAME)
model.eval()

def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output.last_hidden_state
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return (
        torch.sum(token_embeddings * input_mask_expanded, dim=1)
        / torch.clamp(input_mask_expanded.sum(dim=1), min=1e-9)
    )

vectors = []
metadata_store = []

with torch.no_grad():
    for idx, chunk in enumerate(pdf_chunks):

        text = chunk["text"]

        encoded = tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="pt"
        )

        model_output = model(**encoded)
        embedding = mean_pooling(model_output, encoded["attention_mask"])
        vector = embedding.squeeze().numpy().astype("float32")

        vectors.append(vector)

        metadata_store.append({
            "vector_id": idx,
            "job_id": chunk.get("job_id"),
            "chunk_id": chunk.get("chunk_id"),
            "source_file": chunk.get("source_file"),
            "folder": chunk.get("folder"),
            "text": text,
            "metadata": chunk.get("metadata", {})
        })

        if (idx + 1) % 50 == 0 or (idx + 1) == len(pdf_chunks):
            print(f"Embedded {idx + 1}/{len(pdf_chunks)} chunks")


vectors = np.array(vectors, dtype="float32")
faiss.normalize_L2(vectors)

dim = vectors.shape[1]
index = faiss.IndexFlatIP(dim)
index.add(vectors)

faiss.write_index(index, FAISS_INDEX_FILE)
print(f"FAISS index saved: {FAISS_INDEX_FILE}")

with open(METADATA_FILE, "w", encoding="utf-8") as f:
    json.dump(metadata_store, f, indent=2, ensure_ascii=False)

print(f"Metadata saved: {METADATA_FILE}")






