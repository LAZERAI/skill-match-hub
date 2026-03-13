import json
import re
from datetime import datetime

INPUT_FILE = "steps1_raw_text.json"
OUTPUT_FILE = "step2_sections.json"

SKILL_KEYWORDS = [
    "tools & skills", "technical skills", "core competencies",
    "skills", "competencies", "expertise", "technologies","S K I L L S"
]

EXP_KEYWORDS = [
    "professional experience", "work experience", "experience",
    "employment history", "work history","E X P E R I E N C E"
]

PROJECT_KEYWORDS = ["projects"]
EDUCATION_KEYWORDS = ["educational", "education","E D U C A T I O N"]

LANGUAGES = {
    "english", "hindi", "tamil", "malayalam",
    "french", "spanish", "german", "arabic", "urdu"
}


def extract_section_by_keywords(text, start_keywords, end_keywords=None):
    start_pattern = r'(?i)\b(' + '|'.join(re.escape(k) for k in start_keywords) + r')\b'

    start_match = re.search(start_pattern, text)
    if not start_match:
        return ""

    start_pos = start_match.end()

    if end_keywords:
        end_pattern = r'(?i)\b(' + '|'.join(re.escape(k) for k in end_keywords) + r')\b'
        end_match = re.search(end_pattern, text[start_pos:])
        if end_match:
            end_pos = start_pos + end_match.start()
        else:
            end_pos = len(text)
    else:
        end_pos = len(text)

    return text[start_pos:end_pos].strip()


def extract_skills(text):
    all_section_keywords = (SKILL_KEYWORDS + EXP_KEYWORDS +
                            PROJECT_KEYWORDS + EDUCATION_KEYWORDS)

    skills_text = extract_section_by_keywords(
        text,
        SKILL_KEYWORDS,
        [k for k in all_section_keywords if k not in SKILL_KEYWORDS]
    )

    if not skills_text:
        return ""

    parts = re.split(r'[|\n•]', skills_text)
    clean_skills = []

    for part in parts:
        part = part.strip()
        if (part and len(part) > 2 and
                part.lower() not in LANGUAGES and
                not re.match(r'^[\d\s\-]+$', part)):
            clean_skills.append(part)

    return " | ".join(clean_skills[:50])

def extract_experience_section(text):
    all_keywords = SKILL_KEYWORDS + EXP_KEYWORDS + PROJECT_KEYWORDS + EDUCATION_KEYWORDS

    exp_text = extract_section_by_keywords(
        text,
        EXP_KEYWORDS,
        [k for k in all_keywords if k not in EXP_KEYWORDS]
    )

    return exp_text


def calculate_experience_years(text):
    if not text:
        return {
            "experience_years": 0.0,
            "internship_years": 0.0,
            "total_experience_years": 0.0
        }

    text = text.replace("–", "-").replace("—", "-")

    total_months = 0

    def add_months(start_year, start_month, end_year, end_month):
        return (end_year - start_year) * 12 + (end_month - start_month)

    pattern_mm = re.compile(
        r'(\d{1,2})/(\d{4})\s*-\s*(\d{1,2})?/?(\d{4}|Present|Current)',
        re.IGNORECASE
    )

    pattern_month = re.compile(
        r'([A-Za-z]+)\s*(\d{4})\s*[-–—]\s*([A-Za-z]+)?\s*(\d{4}|Present|Current)',
        re.IGNORECASE
    )

    for m in pattern_mm.finditer(text):
        sm, sy, em, ey = m.groups()

        try:
            start_month = int(sm)
            start_year = int(sy)

            if ey.lower() in ["present", "current"]:
                now = datetime.now()
                end_year = now.year
                end_month = now.month
            else:
                end_year = int(ey)
                end_month = int(em) if em else 12

            months = add_months(start_year, start_month, end_year, end_month)

            if months > 0:
                total_months += months

        except:
            continue

    for m in pattern_month.finditer(text):
        sm_name, sy, em_name, ey = m.groups()

        try:
            start_month = datetime.strptime(sm_name[:3], "%b").month
            start_year = int(sy)

            if ey.lower() in ["present", "current"]:
                now = datetime.now()
                end_year = now.year
                end_month = now.month
            else:
                end_year = int(ey)
                end_month = datetime.strptime(em_name[:3], "%b").month if em_name else 12

            months = add_months(start_year, start_month, end_year, end_month)

            if months > 0:
                total_months += months

        except:
            continue

    return {
        "experience_years": round(total_months / 12, 1),
        "internship_years": 0.0,
        "total_experience_years": round(total_months / 12, 1)
    }

def extract_name(text, filename=""):
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    email_match = re.search(
        r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',
        text
    )

    search_area = text[:email_match.start()] if email_match else text[:100]

    caps_match = re.match(
        r'^([A-Z]{2,}(?:\s+[A-Z]{2,}){1,3})\b',
        search_area
    )
    if caps_match:
        return caps_match.group(1).title()
    title_match = re.search(
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b',
        search_area
    )
    if title_match:
        return title_match.group(1)
    return (
        filename.replace('.pdf', '')
        .replace('_', ' ')
        .replace('CV', '')
        .strip()
        .title()
    )

def extract_email(text):
    match = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
    return match.group(0) if match else "Not found"


def run():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        resumes = json.load(f)

    results = []

    for r in resumes:
        text = r["raw_text"]

        skills = extract_skills(text)
        experience_section = extract_experience_section(text)
        experience_data = calculate_experience_years(text)

        result = {
            "resume_id": r["resume_id"],
            "filename": r["filename"],
            "file_path": r.get("file_path", ""),
            "raw_text": text,
            "name": extract_name(text, r["filename"]),
            "email": extract_email(text),
            "skills": skills,
            "experience_section": experience_section[:1000] if experience_section else "",
            **experience_data
        }

        results.append(result)

        print(f"{r['filename']}")
        print(f"  Name: {result['name']}")
        print(f"  Email: {result['email']}")
        print(f"  Total Experience: {experience_data['total_experience_years']} years")
        print()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    run()

