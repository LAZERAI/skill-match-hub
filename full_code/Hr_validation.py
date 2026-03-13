import json
import re

INPUT_FILE = "step3_llm_output.json"
OUTPUT_FILE = "step4_validated.json"


def validate_email(email):
    if not email:
        return "Not found"
    m = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', email)
    return m.group(0) if m else "Not found"


def clean_skills(skills):
    if not skills or not isinstance(skills, list):
        return []
    clean = []
    for s in skills:
        s = str(s).strip().strip(",.;:")
        if s:
            clean.append(s)
    return list(set(clean))


def validate_experience(exp):
    try:
        exp = float(exp)
        return min(max(exp, 0), 40)
    except:
        return 0.0

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

results = []

for r in data:

    extracted = r.get("extracted", r)

    name = extracted.get("name", "Unknown")
    email = validate_email(extracted.get("email", ""))
    skills = clean_skills(extracted.get("skills", []))
    experience_years = validate_experience(extracted.get("experience_years", 0))
    internship_years = validate_experience(extracted.get("internship_years", 0))
    total_experience_years = validate_experience(extracted.get("total_experience_years", 0))

    file_path = r.get("file_path") or r.get("File_path", "")

    results.append({
        "resume_id": r.get("resume_id", ""),
        "filename": r.get("filename", ""),
        "raw_text": r.get("raw_text", ""),
        "file_path": file_path,
        "name": name,
        "email": email,
        "skills": skills,
        "experience_years": experience_years,
        "internship_years": internship_years,
        "total_experience_years": total_experience_years
    })

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f" Validation complete, saved to {OUTPUT_FILE}")
print(f"Total resumes: {len(results)}")