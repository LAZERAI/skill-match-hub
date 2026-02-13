# AI-Powered-Job-Matching-Platform-LLM-Based-Application
Developed an AI-powered job matching platform using Llama 3.3 and Hugging Face embeddings to intelligently connect job seekers with hiring teams through semantic resume–job matching.

#  HR Selection Detection System

An intelligent Resume Parsing and Experience Calculation system built using Python.  
This project extracts structured information from resumes and calculates total professional experience accurately across multiple date formats.

---

## Features

Extracts:
- Name
- Skills
- Work Experience
- Internship Experience
- Total Experience (Years)

Supports Multiple Date Formats:
- `08/2024 - Present`
- `06/2021 - 04/2024`
- `Aug 2021 – Present`
- `Jan 2019 – June 2021`
- `Feb2020 – Present`
- `2021 - 2024`

 Handles:
- Unicode dashes (– — −)
- No-space formats (`Feb2020`)
- Overlapping roles (configurable logic)
- Internship detection

---

## Tech Stack

- Python 3.x
- Regular Expressions (re)
- datetime module
- PDF parsing (if integrated: PyPDF2 / pdfplumber / pytesseract)
- NLP preprocessing (optional)

---


---

## How It Works

1. Extract text from resume (PDF).
2. Normalize section headers.
3. Extract:
   - Name (via regex + email positioning logic)
   - Skills (section-based extraction)
   - Experience dates (multi-format regex)
4. Calculate total experience in months.
5. Convert to years with precision.

---

## Experience Calculation Logic

The system:

- Detects multiple date formats
- Converts dates into month ranges
- Calculates duration
- Handles "Present" dynamically
- Returns:

```json
{
  "experience_years": 4.6,
  "internship_years": 0.5,
  "total_experience_years": 5.1
}

git clone https://github.com/your-username/hr-selection-detection.git
cd hr-selection-detection
pip install -r requirements.txt

python Hr_selection_detection.py

