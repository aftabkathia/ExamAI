from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, inspect

from app.config import get_settings
from app.database import Base, engine
from app.seed import seed_exams
from app.seed_content import seed_learning_content
from app.routers import auth, exams, quiz, progress, learn, chat, workspace, doc_intel

settings = get_settings()

app = FastAPI(
    title="ExamAI API",
    description="Adaptive test preparation for Pakistani competitive & government exams",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(exams.router, prefix="/api")
app.include_router(quiz.router, prefix="/api")
app.include_router(progress.router, prefix="/api")
app.include_router(learn.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(workspace.router, prefix="/api")
app.include_router(doc_intel.router, prefix="/api")


def _migrate_sqlite():
    """Add new columns/tables safely for existing SQLite DBs."""
    Base.metadata.create_all(bind=engine)
    insp = inspect(engine)
    if "quiz_sessions" in insp.get_table_names():
        cols = {c["name"] for c in insp.get_columns("quiz_sessions")}
        if "preferred_topic_id" not in cols:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE quiz_sessions ADD COLUMN preferred_topic_id INTEGER"
                    )
                )


@app.on_event("startup")
def on_startup():
    _migrate_sqlite()
    seed_exams()
    seed_learning_content()


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "ExamAI", "version": "1.2.0"}
