# AI Personal Tutor (Console + Optional Streamlit)

A lightweight, adaptive tutor you can run locally. Starts as a console app; optional Streamlit dashboard is included.

## Quick Start (Console)
```bash
# Windows (PowerShell)
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-min.txt
python console_tutor.py

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-min.txt
python3 console_tutor.py
```

## Optional: Streamlit Dashboard
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Files
- `console_tutor.py` — main console app.
- `engine.py` — question selection, grading, adaptive difficulty.
- `data/questions.json` — starter Class 11 question bank (Math + Physics).
- `streamlit_app.py` — simple dashboard + quiz UI (optional).
- `requirements-min.txt` — only what's needed to run the console.
- `requirements.txt` — for console + Streamlit dashboard.

## Data & Progress
After first run, user progress is stored under `data/progress.json`.
