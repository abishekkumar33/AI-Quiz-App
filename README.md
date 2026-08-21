# AI Quiz & Mock Interview

A full-stack Flask web app for AI-generated quizzes and mock interviews, powered by Google Gemini.

## Features
- Secure registration/login (hashed passwords via Flask-Bcrypt)
- AI Quiz Generator — topic, difficulty, question count, one-question-at-a-time UI, timer, progress bar
- AI Mock Interview — role, experience level, per-answer AI evaluation (score, strengths, weaknesses, improved answer, tips)
- Performance Analysis dashboard with Chart.js (trend, topic-wise, difficulty-wise)
- History with search + CSV export
- PDF report downloads for quizzes and interviews (ReportLab)
- Profile management (update info, change password)
- Bootstrap 5 responsive UI, sidebar + topbar navigation, dark/light mode toggle

## Quick Start

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
# Edit .env and set GEMINI_API_KEY (get one at https://aistudio.google.com/apikey)
# The app works without a key too — it falls back to demo content so you can explore the UI.

# 4. Run the app (SQLite database is created automatically)
python app.py
```

Visit **http://localhost:5000**.

## Using MySQL instead of SQLite
Uncomment and edit the `DATABASE_URL` line in `.env`:
```
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/ai_quiz_app
```
Create the database first (`CREATE DATABASE ai_quiz_app;`), then run `python app.py` — tables are created automatically.

## Project Structure
```
AI-Quiz-App/
├── app.py                 # Application factory & entry point
├── config.py               # Environment-based configuration
├── requirements.txt
├── .env                     # Environment variables (Gemini key, DB URL, secret key)
├── static/
│   ├── css/style.css        # Design tokens + all component styles
│   ├── js/theme.js           # Dark mode + sidebar toggle
│   └── images/
├── templates/                # Jinja2 templates (Bootstrap 5)
├── models/                   # SQLAlchemy models (users, quizzes, interviews...)
├── routes/                   # Flask blueprints (auth, quiz, interview, performance, history, profile)
├── services/
│   ├── gemini_service.py     # All Gemini API calls + JSON parsing + offline fallback
│   └── export_service.py     # PDF (ReportLab) & CSV export
├── database/                  # SQLite file lives here in dev
└── utils/validators.py        # Input validation helpers
```

## Database Tables
`users`, `quizzes`, `quiz_questions`, `quiz_results`, `interviews`, `interview_answers`

## Notes
- If `GEMINI_API_KEY` is not set (or a call fails), the app automatically falls back to locally generated
  demo questions/feedback so every feature remains testable end-to-end without an API key.
- Passwords are hashed with bcrypt; sessions are Flask's signed cookie sessions via Flask-Login.
