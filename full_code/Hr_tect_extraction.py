import os
import json
import re
import pdfplumber

RESUME_FOLDER = "D:/project_2_resumes"
OUTPUT_FILE = "steps1_raw_text.json"

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\x00', '')
    return text.strip()

def extract_from_pdf(path):
    full_text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    full_text += t + "\n"
    except Exception as e:
        print(f"Error reading {path}: {e}")
    return full_text


def run():

    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                all_resumes = json.load(f)
            print(f"Loaded {len(all_resumes)} existing resumes")
        except:
            print("Existing JSON corrupted. Starting fresh.")
            all_resumes = []
    else:
        all_resumes = []

    processed_ids = {r["resume_id"] for r in all_resumes}

    if not os.path.exists(RESUME_FOLDER):
        print("Folder not found!")
        return

    files = [f for f in os.listdir(RESUME_FOLDER)
             if f.lower().endswith((".pdf", ".txt"))]

    print(f"Found {len(files)} resumes in folder")

    new_count = 0

    for file in files:

        if file in processed_ids:
            print(f"Skipping already processed: {file}")
            continue

        path = os.path.join(RESUME_FOLDER, file)

        if file.lower().endswith(".pdf"):
            raw_text = extract_from_pdf(path)
        else:
            with open(path, "r", errors="ignore", encoding="utf-8") as f:
                raw_text = f.read()

        cleaned = clean_text(raw_text)

        if not cleaned:
            print(f"Empty content: {file}")
            continue

        all_resumes.append({
            "resume_id": file,
            "filename": file,
            "file_path": path,
            "raw_text": cleaned
        })

        new_count += 1
        print(f"Processed NEW resume: {file}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_resumes, f, indent=2, ensure_ascii=False)

    print(f"\nAdded {new_count} new resumes.")
    print(f"Total resumes stored: {len(all_resumes)}")

if __name__ == "__main__":
    run()

