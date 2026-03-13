# Skill Match Hub — Frontend + Backend Integration

Build a complete web frontend for Rijin's AI-Powered Job Matching Platform. The app connects job seekers with recruiters using FAISS vector search + Groq LLM (Llama 3.3) for semantic matching and evaluation.

## User Review Required

> [!IMPORTANT]
> **GROQ_API_KEY required** — The backend needs a valid Groq API key in [.env](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/.env). Rijin's existing FAISS indices and metadata JSON files will be bundled with the project.

> [!WARNING]
> **Backend consolidation** — The existing code in `full_code/` has scattered scripts with `tkinter` file dialogs (desktop-only). I'll rewrite into a single FastAPI `app.py` that accepts PDF uploads via HTTP endpoints, making it web-compatible. The core logic (FAISS search, embedding, LLM calls) stays identical.

## Proposed Changes

The new project will be structured cleanly in the root workspace directory, separate from the messy `full_code/` dump.

---

### Backend — FastAPI App

#### [NEW] [app.py](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/app.py)

Single FastAPI server consolidating all backend logic:

- **Startup**: Load both FAISS indices, embedding model, Groq client
  - [resume_faiss.index](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/full_code/resume_faiss.index) + [resume_metadata.json](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/full_code/resume_metadata.json) → for recruiter searching candidates
  - [rag_vector_index.faiss](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/full_code/rag_vector_index.faiss) + [job_description_chunks_metadata.json](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/full_code/job_description_chunks_metadata.json) → for seekers searching jobs
- **Endpoints**:
  - `POST /api/recruiter/search` — Accepts JD text input, searches resume FAISS index, matches & ranks candidates, runs LLM evaluation on top results
  - `POST /api/seeker/search` — Accepts resume text input, searches job description FAISS index, returns top job matches with career advice from LLM
  - `GET /api/health` — Health check
  - `GET /` — Serves frontend

> **Key change**: Instead of PDF file uploads (which need file handling on server), I'll use text input fields where users paste their JD/resume text. This is simpler and works everywhere including HuggingFace Spaces.

---

### Frontend — Vanilla HTML/CSS/JS

#### [NEW] [index.html](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/static/index.html)

Three-view single-page app:
1. **Landing / Role Selection** — Clean split-screen with "I'm a Recruiter" and "I'm a Job Seeker" cards
2. **Recruiter Dashboard** — Paste job description → get ranked candidates with LLM evaluation cards
3. **Job Seeker Dashboard** — Paste resume text → get matched jobs with career analysis

#### [NEW] [style.css](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/static/style.css)

- **LinkedIn color palette**: Primary `#0A66C2` (LinkedIn blue), secondary `#004182`, accent `#70B5F9`
- **Light mode default** with dark mode toggle
- CSS custom properties for theming, glassmorphism effects, micro-animations
- Responsive design (mobile-friendly)
- Premium card-based layout for results

#### [NEW] [script.js](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/static/script.js)

- View switching (landing → recruiter/seeker dashboard)
- Theme toggle with localStorage persistence
- API calls to backend with loading states
- Result card rendering with LLM evaluation formatting
- Smooth animations and transitions

---

### Project Files

#### [NEW] [requirements.txt](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/requirements.txt)

```
fastapi
uvicorn
groq
faiss-cpu
sentence-transformers
torch
transformers
numpy
python-dotenv
```

#### [NEW] [README.md](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/README.md)

Updated with project description, setup instructions, features, and credits.

#### [NEW] [.gitignore](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/.gitignore)

Standard Python `.gitignore` + [.env](file:///c:/Users/Lazerai/Downloads/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/AI-Powered-Job-Matching-Platform-LLM-Based-Application-main/.env) exclusion.

---

## Verification Plan

### Manual Verification (by user)
1. Run `pip install -r requirements.txt` and `uvicorn app:app --reload --port 8000`
2. Open `http://localhost:8000` — verify landing page shows with role selection
3. Click "Recruiter" → paste a job description → verify candidate results appear
4. Click "Job Seeker" → paste resume text → verify job matches appear
5. Toggle dark/light mode → verify theme switches smoothly
6. Verify responsive behavior on mobile viewport

### Deployment Verification
1. Push to GitHub via `gh` CLI → verify repo exists at `github.com/LAZERAI/...`
2. Verify Rijin (Rijin-shaji) is added as collaborator
