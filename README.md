---
title: Skill Match Hub
emoji: 🎯
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# Skill Match Hub

Skill Match Hub is a job matching platform that utilizes semantic search and Large Language Models to connect candidates with relevant opportunities. It leverages Groq (Llama 3.3) and FAISS to provide context-aware matching beyond simple keyword searches.

## Features

- **Semantic Evaluation**: Uses Sentence Transformers to identify skill alignment between resumes and job descriptions.
- **Recruiter Insights**: Automated evaluation of candidate fit for specific roles.
- **Candidate Guidance**: Personalized feedback on job suitability and skill development.
- **Responsive Interface**: Modern web UI with support for both light and dark themes.
- **FastAPI Backend**: Optimized server for efficient query processing.

## Tech Stack

- **Frontend**: Vanilla JavaScript, HTML5, CSS3.
- **Backend**: FastAPI, Uvicorn.
- **AI/ML**: FAISS, Sentence Transformers (all-MiniLM-L6-v2), Groq API.
- **Deployment**: Docker, HuggingFace Spaces.

## Installation

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
   Create a `.env` file with your Groq API key:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

4. **Run the application**:
   ```bash
   uvicorn app:app --reload
   ```
   The application will be available at `http://localhost:8000`.

## Credits

- **Original Logic & Data**: Rijin Shaji ([@Rijin-shaji](https://github.com/Rijin-shaji))
- **Frontend & Integration**: LAZERAI

## License

This project is licensed under the MIT License.
