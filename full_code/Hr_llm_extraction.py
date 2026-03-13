import json
import re
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

INPUT_FILE = "step2_sections.json"
OUTPUT_FILE = "step3_llm_output.json"
LLM_MODEL_NAME = "llama-3.3-70b-versatile"

api_key = os.getenv("GROQ_API")
if not api_key:
    raise ValueError("GROQ_API environment variable not set")

client = Groq(api_key=api_key)

PROMPT = """
Extract professional and technical skills from the following resume text.

Rules:
- Extract ONLY technical skills, tools, programming languages, frameworks, certifications
- Return short phrases (2-5 words maximum)
- NO full sentences
- NO soft skills like "communication" or "teamwork"

Return ONLY a JSON array of skills (NO markdown, NO code blocks):
["skill1", "skill2", "skill3"]

Resume text:
"""

SKILLS_HEADERS = [
    "skills", "technical skills", "competencies", "expertise",
    "tools", "technologies", "projects", "certifications"
]


def combine_skill_sections(r):
    skills_text = ""
    for key, val in r.items():
        if isinstance(val, str) and any(sh in key.lower() for sh in SKILLS_HEADERS):
            skills_text += val + " "
    return skills_text.strip()


def clean_llm_json(content):
    if content.startswith("```"):
        content = re.sub(r'^```(?:json)?\n?', '', content)
        content = re.sub(r'\n?```$', '', content)
    return content.strip()


def run():
    with open(INPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)

    results = []

    for r in data:
        resume_id = r.get("resume_id", "")
        filename = r.get("filename", "")

        file_path = r.get("file_path") or r.get("File_path") or ""

        name = r.get("name", "Unknown")
        email = r.get("email", "")

        print("-----")
        print("Processing:", filename)
        print("DEBUG File_path from Step2:", r.get("File_path"))
        print("DEBUG file_path from Step2:", r.get("file_path"))
        print("FINAL file_path USED:", file_path)

        skills_text = combine_skill_sections(r)
        if not skills_text:
            skills_text = r.get("raw_text", "")[:2000]

        experience_section = r.get("experience_section", "")
        llm_input = f"{skills_text}\n\n{experience_section}"

        try:
            response = client.chat.completions.create(
                model=LLM_MODEL_NAME,
                messages=[{"role": "user", "content": PROMPT + llm_input}],
                temperature=0
            )

            content = response.choices[0].message.content.strip()
            content = clean_llm_json(content)
            skills_list = json.loads(content)

            if not isinstance(skills_list, list):
                skills_list = []

        except Exception as e:
            print("ERROR extracting skills:", e)
            skills_list = []

        final_result = {
            "resume_id": resume_id,
            "filename": filename,
            "file_path": file_path,
            "name": name,
            "email": email,
            "skills": skills_list,
            "experience_years": r.get("experience_years", 0.0),
            "internship_years": r.get("internship_years", 0.0),
            "total_experience_years": r.get("total_experience_years", 0.0)
        }

        results.append(final_result)

        print("Skills Extracted:", len(skills_list))
        print("Experience:", final_result["total_experience_years"], "years")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n Complete! Saved to", OUTPUT_FILE)
    print("Total resumes processed:", len(results))


if __name__ == "__main__":
    run()


