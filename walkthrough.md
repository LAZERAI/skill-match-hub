# Skill Match Hub — Walkthrough

## What Was Built

A complete web frontend + unified backend for Rijin's AI-Powered Job Matching Platform.

### Files Created

| File | Purpose |
|------|---------|
| [app.py](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/app.py) | FastAPI backend — consolidated all scattered scripts into one file |
| [index.html](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/static/index.html) | Three-view SPA: Landing → Recruiter / Job Seeker |
| [style.css](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/static/style.css) | LinkedIn-blue themed CSS with light/dark mode |
| [script.js](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/static/script.js) | View switching, API calls, result rendering |
| [README.md](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/README.md) | Project docs with credits to both contributors |
| [requirements.txt](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/requirements.txt) | Python dependencies |
| [.gitignore](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/.gitignore) | Standard Python gitignore |

---

## UI Flow

1. **Landing page** — "Skill Match Hub" branding with two role cards (Recruiter / Job Seeker)
2. **Recruiter dashboard** — Paste JD → AI returns ranked candidates with LLM evaluation (Hire/Consider/Reject badges)
3. **Seeker dashboard** — Paste resume → AI returns matched jobs with career analysis

**Theme**: LinkedIn blue (`#0A66C2`), light mode default, dark mode toggle available everywhere.

---

## GitHub Deployment

- **Repo**: [github.com/LAZERAI/skill-match-hub](https://github.com/LAZERAI/skill-match-hub)
- **Rijin** (`Rijin-shaji`) invited as collaborator with push access ✓

---

## How to Run

```bash
cd skill-match-hub
pip install -r requirements.txt
# Add GROQ_API_KEY to .env
uvicorn app:app --reload --port 8000
# Open http://localhost:8000
```
