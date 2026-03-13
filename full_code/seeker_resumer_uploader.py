import os
import json
import faiss
import torch
import numpy as np
import PyPDF2
import tkinter as tk
from tkinter import filedialog
from transformers import AutoTokenizer, AutoModel

FAISS_INDEX_PATH = "rag_vector_index.faiss"
METADATA_PATH = "job_description_chunks_metadata.json"
HF_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K = 5

index = faiss.read_index(FAISS_INDEX_PATH)
print("FAISS index loaded")

with open(METADATA_PATH, "r", encoding="utf-8") as f:
    metadata_store = json.load(f)

print(f"Loaded {len(metadata_store)} metadata entries")


tokenizer = AutoTokenizer.from_pretrained(HF_MODEL_NAME)
model = AutoModel.from_pretrained(HF_MODEL_NAME)
model.eval()

def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output.last_hidden_state
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, dim=1) / torch.clamp(
        input_mask_expanded.sum(dim=1), min=1e-9
    )

def embed_text(text):
    encoded_input = tokenizer(
        text,
        padding=True,
        truncation=True,
        max_length=256,
        return_tensors="pt"
    )
    with torch.no_grad():
        model_output = model(**encoded_input)
        embedding = mean_pooling(model_output, encoded_input["attention_mask"])

    vector = embedding.squeeze().numpy().astype("float32")
    norm = np.linalg.norm(vector)
    if norm != 0:
        vector = vector / norm
    return vector.reshape(1, -1)


def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def upload_resume():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    file_path = filedialog.askopenfilename(
        title="Select Resume PDF",
        filetypes=[("PDF Files", "*.pdf")]
    )

    root.destroy()
    return file_path


def search_faiss(vector, top_k=TOP_K):
    scores, indices = index.search(vector, top_k)
    results = []

    for idx, score in zip(indices[0], scores[0]):
        if idx >= len(metadata_store):
            continue

        entry = metadata_store[idx]
        results.append({
            "similarity_score": float(score),
            "text": entry.get("text", ""),
            "metadata": entry.get("metadata", {})
        })

    return results


def retrieve_resume_matches():
    print("\nUpload your resume PDF...")
    pdf_path = upload_resume()

    if not pdf_path:
        print("No file selected")
        return None

    print(f"Resume uploaded: {os.path.basename(pdf_path)}")

    resume_text = extract_text_from_pdf(pdf_path)
    if not resume_text.strip():
        print("Resume is empty")
        return None

    resume_vector = embed_text(resume_text)
    top_matches = search_faiss(resume_vector)

    return top_matches


if __name__ == "__main__":
    matches = retrieve_resume_matches()

    if matches:
        print("\n===== TOP MATCHED JOB CHUNKS =====\n")
        for match in matches:
            md = match.get("metadata", {})
            print(f"Job Title : {md.get('job_title', 'Unknown')}")
            print(f"Company   : {md.get('company', 'Unknown')}")
            print(f"Location  : {md.get('location', 'Unknown')}")
            print(f"Score     : {match['similarity_score']:.4f}")
            print(f"Text      : {match['text'][:300]}...\n")



