# ExamAI

Adaptive test preparation for Pakistan's competitive & government job exams.

AI-generated MCQs · adaptive difficulty · progress dashboard · AI Tutor (PDF & image upload) · email/password & Google auth.

## Stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS, Framer Motion |
| Backend | FastAPI, SQLAlchemy, SQLite |
| AI | Groq API (Llama 3.3) with local fallback bank |

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # or: cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Optional: set `GROQ_API_KEY` in `backend/.env` for live LLM questions. Without it, the app uses a built-in MCQ bank so everything still works offline.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 3. Google sign-in (optional)

1. Create an OAuth client in Google Cloud Console.
2. Set `GOOGLE_CLIENT_ID` in `backend/.env` and `NEXT_PUBLIC_GOOGLE_CLIENT_ID` in `frontend/.env.local`.

## Features

- **Auth** — register / login with email & password; optional Google OAuth
- **Dual tracks** — Academic (CSS, MDCAT, ECAT, NET) and Government (NTS, PPSC, FPSC, OTS)
- **Adaptive quizzes** — weaker topics get higher selection weight; difficulty scales with mastery
- **Instant explanations** — plain-language feedback after every answer
- **Dashboard** — accuracy, streaks, 14-day activity, topic mastery table
- **AI Assistant** — multilingual chat (English, Urdu, Roman Urdu); **voice in/out**; PDF & image upload
- **Notes / Essays / Past papers** — study content per topic

## API

- `POST /api/auth/register` · `POST /api/auth/login` · `GET /api/auth/me`
- `GET /api/exams` · `GET /api/exams/{id}`
- `POST /api/quiz/start` · `POST /api/quiz/answer`
- `GET /api/progress/dashboard`
- `POST /api/chat/` · `POST /api/chat/upload` (multipart PDF/images) · `GET /api/chat/suggestions`
- Docs: [http://localhost:8001/docs](http://localhost:8001/docs)

## Project layout

```
Examai/
├── backend/app/          # FastAPI app, models, adaptive engine, Groq service
├── frontend/src/         # Next.js App Router UI
└── README.md
```
