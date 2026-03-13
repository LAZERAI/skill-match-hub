import os
import json
import re
import PyPDF2
import nltk
from nltk.tokenize import sent_tokenize

nltk.download("punkt")


def extract_metadata_from_header(text, filename):
    company = "Unknown"
    job_title = filename.replace(".pdf", "")
    location = "Unknown"

    lines = text.splitlines()[:20]
    header_text = "\n".join(lines)


    company_match = re.search(r'(?i)(?:Company|Organization)\s*[:\-\.]?\s+(.*)', header_text)
    if company_match:
        company = company_match.group(1).strip()

    job_match = re.search(r'(?i)(?:Job\s+(?:Title|Role)|Position|Role)\s*[:\-\.]?\s+(.*)', header_text)
    if job_match:
        job_title = job_match.group(1).strip()

    location_match = re.search(r'(?i)(?:Location|Loc|Address)\s*[:\-\.]?\s+(.*)', header_text)
    if location_match:
        location = location_match.group(1).strip()

    return company, job_title, location


def preprocess_pdfs(root_folder_path, chunk_size=6, overlap=2):
    job_chunks = []

    for foldername, _, filenames in os.walk(root_folder_path):
        for filename in filenames:
            if not filename.lower().endswith(".pdf"):
                continue

            pdf_path = os.path.join(foldername, filename)

            text = ""
            with open(pdf_path, "rb") as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            if not text.strip():
                continue

            company, job_title, location = extract_metadata_from_header(text, filename)

            sentences = sent_tokenize(text)
            start = 0
            chunk_id = 1

            while start < len(sentences):
                chunk_text = " ".join(sentences[start:start + chunk_size])

                job_chunks.append({
                    "job_id": filename.replace(".pdf", ""),
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "source_file": filename,
                    "folder": foldername,
                    "metadata": {
                        "job_title": job_title,
                        "company": company,
                        "location": location
                    }
                })

                chunk_id += 1
                start += chunk_size - overlap

    return job_chunks


if __name__ == "__main__":
    root_folder = "D:/Project_2"
    chunks = preprocess_pdfs(root_folder)

    print(f"Total chunks created: {len(chunks)}")
    if chunks:
        print("Sample chunk:")
        print(json.dumps(chunks[0], indent=2, ensure_ascii=False))

    output_file = "job_description_chunks.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(chunks)} chunks to {output_file}")


