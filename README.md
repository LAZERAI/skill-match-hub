# Skill Match Hub

AI-powered job matching platform using **Llama 3.3 70B** and **FAISS** vector search to connect recruiters with top candidates and job seekers with the best opportunities.

Built with FastAPI + vanilla HTML/CSS/JS frontend.

---

## Features

- **Dual-role interface** — Recruiter and Job Seeker modes
- **Semantic matching** — FAISS vector search with sentence-transformers (MiniLM-L6-v2)
- **AI evaluation** — Llama 3.3 70B via Groq for candidate assessment and career analysis
- **Light/Dark theme** — LinkedIn-inspired design with theme toggle
- **Responsive** — Works on desktop and mobile

---

## How It Works

### Recruiter Flow
1. Paste a job description
2. System embeds JD → searches resume FAISS index
3. Matches & ranks candidates by skill overlap + semantic similarity
4. Llama 3.3 evaluates each candidate (Summary, Strengths, Gaps, Recommendation)

### Job Seeker Flow
1. Paste your resume text
2. System embeds resume → searches job description FAISS index
3. Returns top matching positions
4. Llama 3.3 provides career analysis for each match

---

## Stack

- Python 3.11+
- FastAPI + Uvicorn
- FAISS for vector search
- sentence-transformers for embeddings
- Groq API (Llama 3.3 70B)
- Vanilla HTML/CSS/JS frontend

---

## Getting Started

```bash
git clone https://github.com/LAZERAI/skill-match-hub.git
cd skill-match-hub
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

Create a `.env` file:

```
GROQ_API_KEY=your_key_here
```

Get a free key at [console.groq.com](https://console.groq.com)

Run:

```bash
uvicorn app:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000)

---

## Project Structure

```
├── app.py                              # FastAPI backend
├── static/
│   ├── index.html                      # Frontend UI
│   ├── style.css                       # LinkedIn-themed styles
│   └── script.js                       # Frontend logic
├── full_code/
│   ├── resume_faiss.index              # Resume vector index
│   ├── resume_metadata.json            # Resume metadata
│   ├── rag_vector_index.faiss          # Job description vector index
│   ├── job_description_chunks_metadata.json
│   └── ...                             # Original pipeline scripts
├── requirements.txt
├── .env                                # API key (not committed)
└── README.md
```

---

## Credits

- **Backend & AI Pipeline**: [Rijin Shaji](https://github.com/Rijin-shaji)
- **Frontend & Integration**: [LAZERAI](https://github.com/LAZERAI)

## License

MIT
