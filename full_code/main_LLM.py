import os
from groq import Groq
from Hr_pdf_reading import find_best_employees
from seeker_resumer_uploader import retrieve_resume_matches

LLM_MODEL = "llama-3.3-70b-versatile"

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not set")

llm_client = Groq(api_key=api_key)

def seeker_analysis(job_match):
    metadata = job_match.get("metadata", {})

    company = metadata.get("company", "Not provided")
    role = metadata.get("job_title", "Not provided")
    location = metadata.get("location", "Not provided")

    prompt = f"""
You are a career advisor.

Company Name: {company}
Job Role: {role}
Location: {location}

Job Description (supporting context only):
{job_match.get("text", "")}
"""
    return prompt

def hr_evaluation(candidate):
    prompt = f"""
You are an HR evaluator.

Candidate Information (trusted):
Name: {candidate.get("name")}
Email: {candidate.get("email")}
Experience Years: {candidate.get("experience_years")}
InterShip Years: {candidate.get("internship_years")}
Total Experiences: {candidate.get("total_experience_years")}
Skills: {", ".join(candidate.get("skills", []))}
Matched Skills: {", ".join(candidate.get("matched_skills", []))}

Evaluate ONLY:
1. Candidate Summary
2. Strengths
3. Skill Gaps
4. Hiring Recommendation (Hire / Consider / Reject)

Do NOT hallucinate.
"""

    response = llm_client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": "You are a strict HR analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=350
    )

    return response.choices[0].message.content

def main():
    while True:
        print("\nWho are you?")
        print("1. Job Seeker")
        print("2. HR / Recruiter")
        print("0. Exit")

        choice = input("Enter 1, 2 or 0: ").strip()

        if choice == "0":
            print("Exiting application. Goodbye!!")
            break

        elif choice == "1":
            matches = retrieve_resume_matches()

            if not matches:
                print("No job matches found")
                continue

            print("\n===== TOP JOB MATCHES =====\n")
            for i, match in enumerate(matches[:3], 1):
                print("=" * 60)
                print(f"MATCH #{i} | Score: {match['similarity_score']:.4f}\n")
                print(seeker_analysis(match))

        elif choice == "2":
            candidates = find_best_employees()

            if not candidates:
                print("No suitable candidates found")
                continue

            print("\n===== TOP CANDIDATES =====\n")
            for i, cand in enumerate(candidates[:6], 1):
                print("=" * 60)
                print(f"Rank               : {i}")
                print(f"Name               : {cand.get('name')}")
                print(f"Email              : {cand.get('email')}")
                print(f"Resume Path        : {cand.get('file_path', 'Not available')}")
                print(f"Skills             : {cand.get('skills')}")
                print(f"InternShip         : {cand.get('internship_years')} years")
                print(f"Experience         : {cand.get('experience_years')} years")
                print(f"Total Experiences  : {cand.get('total_experience_years')} years")
                print(hr_evaluation(cand))

        else:
            print("Invalid choice. Please enter 1, 2, or 0.")

if __name__ == "__main__":
    main()




