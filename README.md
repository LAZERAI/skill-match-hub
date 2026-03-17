# Skill Match Hub — AI-Powered Job Matching

**Skill Match Hub** is a next-generation recruitment platform that uses semantic search and Large Language Models (LLMs) to connect talent with opportunities. 

Powered by **Groq (Llama 3.3)** and **FAISS**, this platform goes beyond keyword matching to understand the context and meaning of resumes and job descriptions.

## 🚀 Features

- **Semantic Match Evaluation**: Uses Sentence Transformers to understand deep skill alignment.
- **AI Analysis for Recruiters**: LLM-driven evaluation of candidates' fit for a role.
- **Career Advice for Seekers**: Personalized insights on why a job fits and how to prepare.
- **Modern UI**: Clean, LinkedIn-inspired interface with responsive design and theme support (Dark/Light).
- **Consolidated Backend**: Fast and efficient FastAPI server.

## 🛠️ Tech Stack

- **Frontend**: Vanilla JS, HTML5, CSS3 (Custom properties for theming).
- **Backend**: FastAPI, Uvicorn.
- **AI/ML**: FAISS, Sentence Transformers (all-MiniLM-L6-v2), Groq API (Llama 3.3).
- **Deployment**: Docker, HuggingFace Spaces.

## 📦 Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/LAZERAI/skill-match-hub
   cd skill-match-hub
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   Create a `.env` file and add your Groq API key:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

4. **Run the application**:
   ```bash
   uvicorn app:app --reload
   ```
   Open `http://localhost:8000` in your browser.

## 👨‍💻 Credits

- **Original Logic & Data**: Rijin Shaji ([@Rijin-shaji](https://github.com/Rijin-shaji))
- **Frontend & Integration**: LAZERAI

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
