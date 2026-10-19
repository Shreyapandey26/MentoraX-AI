# MentoraX AI

**AI-powered academic performance diagnostic system** built with Django, a RAG pipeline (LangChain + BM25) and Groq LLM.

A raw marksheet tells you the number, not the reason. MentoraX AI takes a student's marks, attendance and weekly study hours, finds *why* the score is what it is, and suggests what to do next.

> Final-year BCA (Data Science & AI) project, BBD University, Lucknow.

---

## Features

- **Performance tiers** - scores are classified as Excellent (75%+), Average (50-74%) or Alert (below 50%).
- **Heuristic diagnostic engine** - rule-based findings on how attendance and study hours relate to performance, plus a recommendation list.
- **RAG-based AI mentoring** - relevant advice is retrieved from a local knowledge base (subject tips, study habits, attendance, tier-specific guidance) and passed to a Groq LLM, which returns a summary, recommendations and a study plan.
- **Marksheet OCR** - upload a marksheet image and Tesseract extracts marks, total, roll number and subject to pre-fill the form. Manual entry also works.
- **Interactive dashboard** - Chart.js doughnut (marks accuracy) and bar (multi-metric) charts with metric cards.
- **Validated input** - custom form validation for marks, attendance and study hours.
- **Record history** - every analysis is stored in the database and visible in Django admin.

> **Note:** the "biometric scan" screen is a simulated fingerprint animation used as a session gate. It does not perform real biometric authentication.

---

## Tech Stack

| Layer | Tools |
|---|---|
| Backend | Python, Django 6 |
| Database | SQLite |
| AI / LLM | Groq API (llama-3.3-70b-versatile) |
| RAG | LangChain, BM25 retriever (rank_bm25), text splitter |
| OCR | Tesseract, pytesseract, Pillow |
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Config | python-dotenv |

---

## How it works

    Scan (session gate) -> Enter name -> Enter marks / upload marksheet
            -> Heuristic engine (tier + findings)
            -> RAG: retrieve top-3 knowledge chunks -> Groq LLM
            -> Dashboard (charts + AI analysis)

The knowledge base lives in the mentor/knowledge/ folder as plain text files. BM25 retrieval means no embedding model downloads, so the app starts quickly.

---

## Project structure

    MentoraX-AI/
    |-- manage.py
    |-- requirements.txt
    |-- .env.example
    |-- GUIDE.md              (detailed module-by-module guide)
    |-- mentorax_ai/          (Django project settings and root URLs)
    |-- mentor/
    |   |-- views.py          (pages, diagnostic engine, OCR endpoint)
    |   |-- models.py         (StudentRecord model)
    |   |-- forms.py          (input validation)
    |   |-- rag_service.py    (LangChain + BM25 + Groq pipeline)
    |   |-- groq_service.py   (Groq client and fallback)
    |   |-- ocr_service.py    (Tesseract OCR and field parsing)
    |   |-- knowledge/        (RAG knowledge base, .txt files)
    |-- templates/
    |-- static/

---

## Getting started

### Prerequisites

- Python 3.12 or newer
- A free Groq API key from https://console.groq.com/keys
- **Tesseract OCR** (only needed for the marksheet upload feature)

### Installation

1. Clone the repository:

        git clone https://github.com/Shreyapandey26/MentoraX-AI.git
        cd MentoraX-AI

2. Create and activate a virtual environment:

        python -m venv venv
        venv\Scripts\activate

    On macOS / Linux, use: source venv/bin/activate

3. Install dependencies:

        pip install -r requirements.txt

### Configure environment variables

Copy .env.example to a new file named .env and fill in your values:

    GROQ_API_KEY=your_groq_api_key
    DJANGO_SECRET_KEY=any_long_random_string

Never commit your .env file. It is already listed in .gitignore.

### Install Tesseract (for OCR)

The pip command installs only the Python wrapper, so the Tesseract program must be installed separately.

- **Windows:** download the installer from the UB Mannheim Tesseract build, install it, and add C:\Program Files\Tesseract-OCR to your PATH. Open a new terminal and check with: tesseract --version
- **Ubuntu / Debian:** sudo apt install tesseract-ocr
- **macOS:** brew install tesseract

If you skip this, marksheet upload will not work, but you can still enter data manually.

### Run

    python manage.py migrate
    python manage.py runserver

Open http://127.0.0.1:8000 in your browser.

Restart the server after editing .env, because environment variables are read only at startup.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| ImportError: Couldn't import Django | Activate the virtual environment, then run pip install -r requirements.txt. |
| 401 Invalid API Key | Check the key in .env, then restart the server. |
| tesseract is not installed or it's not in your PATH | Install Tesseract and reopen your terminal. |
| First AI request is slow | The knowledge index is built on first use; later requests are faster. |

---

## Limitations

- Developer-level college project, not production-ready (DEBUG is on, SQLite database, no real authentication).
- OCR accuracy depends on how clear the marksheet image is.
- Diagnostic rules are heuristic and meant for guidance, not as a formal assessment.

---

## Author

**Shreya Pandey**
GitHub: [@Shreyapandey26](https://github.com/Shreyapandey26)


## License

Released under the MIT License. See the LICENSE file for details.
