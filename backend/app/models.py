from datetime import datetime
from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_practice_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    attempts = relationship("Attempt", back_populates="user")
    topic_mastery = relationship("TopicMastery", back_populates="user")
    quiz_sessions = relationship("QuizSession", back_populates="user")
    chat_messages = relationship("ChatMessage", back_populates="user")
    memories = relationship("UserMemory", back_populates="user")
    workspace_notes = relationship("WorkspaceNote", back_populates="user")
    workspace_tasks = relationship("WorkspaceTask", back_populates="user")
    workspace_documents = relationship("WorkspaceDocument", back_populates="user")
    workspace_whiteboards = relationship("WorkspaceWhiteboard", back_populates="user")
    intel_documents = relationship("IntelDocument", back_populates="user")


class IntelDocument(Base):
    """PDF library for document intelligence (business search)."""

    __tablename__ = "intel_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    filename: Mapped[str] = mapped_column(String(512))
    title: Mapped[str] = mapped_column(String(512))
    doc_kind: Mapped[str] = mapped_column(String(50), default="document")  # invoice|contract|report|other
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    file_hash: Mapped[str] = mapped_column(String(64), index=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="intel_documents")
    chunks = relationship("IntelChunk", back_populates="document", cascade="all, delete-orphan")


class IntelChunk(Base):
    """Searchable text chunk from an uploaded PDF."""

    __tablename__ = "intel_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("intel_documents.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    page_hint: Mapped[str] = mapped_column(String(50), default="")
    text: Mapped[str] = mapped_column(Text)

    document = relationship("IntelDocument", back_populates="chunks")


class WorkspaceNote(Base):
    __tablename__ = "workspace_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(20), default="manual")  # manual | chat
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="workspace_notes")


class WorkspaceTask(Base):
    __tablename__ = "workspace_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="todo")  # todo | doing | done
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="workspace_tasks")


class WorkspaceDocument(Base):
    __tablename__ = "workspace_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    filename: Mapped[str] = mapped_column(String(255))
    mime: Mapped[str] = mapped_column(String(120))
    file_data: Mapped[str] = mapped_column(Text)  # base64
    source: Mapped[str] = mapped_column(String(20), default="generated")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="workspace_documents")


class WorkspaceWhiteboard(Base):
    __tablename__ = "workspace_whiteboards"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_whiteboard"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255), default="My Whiteboard")
    canvas_data: Mapped[str] = mapped_column(Text, default="[]")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="workspace_whiteboards")


class ChatMessage(Base):
    """Persisted tutor chat — powers personal memory across sessions."""

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="chat_messages")


class UserMemory(Base):
    """Long-term facts: preferences, projects, goals, conversation context."""

    __tablename__ = "user_memories"
    __table_args__ = (UniqueConstraint("user_id", "title", name="uq_user_memory_title"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    category: Mapped[str] = mapped_column(String(30), index=True)  # preference|project|goal|fact
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="memories")


class ExamTrack(Base):
    __tablename__ = "exam_tracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(50))  # academic | government
    description: Mapped[str] = mapped_column(Text)
    icon: Mapped[str] = mapped_column(String(50), default="book")

    topics = relationship("Topic", back_populates="exam_track")


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exam_track_id: Mapped[int] = mapped_column(ForeignKey("exam_tracks.id"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")

    exam_track = relationship("ExamTrack", back_populates="topics")
    questions = relationship("Question", back_populates="topic")
    mastery_records = relationship("TopicMastery", back_populates="topic")
    notes = relationship("TopicNote", back_populates="topic")
    essays = relationship("EssayPrompt", back_populates="topic")
    past_papers = relationship("PastPaper", back_populates="topic")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    text: Mapped[str] = mapped_column(Text)
    option_a: Mapped[str] = mapped_column(Text)
    option_b: Mapped[str] = mapped_column(Text)
    option_c: Mapped[str] = mapped_column(Text)
    option_d: Mapped[str] = mapped_column(Text)
    correct_option: Mapped[str] = mapped_column(String(1))  # A|B|C|D
    explanation: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")  # easy|medium|hard
    source: Mapped[str] = mapped_column(String(50), default="llm")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    topic = relationship("Topic", back_populates="questions")
    attempts = relationship("Attempt", back_populates="question")


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    exam_track_id: Mapped[int] = mapped_column(ForeignKey("exam_tracks.id"))
    preferred_topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"), nullable=True)
    total_questions: Mapped[int] = mapped_column(Integer, default=10)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user = relationship("User", back_populates="quiz_sessions")
    attempts = relationship("Attempt", back_populates="session")


class TopicNote(Base):
    __tablename__ = "topic_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[str] = mapped_column(Text)
    key_points: Mapped[str] = mapped_column(Text, default="")  # newline-separated
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    topic = relationship("Topic", back_populates="notes")


class EssayPrompt(Base):
    __tablename__ = "essay_prompts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    title: Mapped[str] = mapped_column(String(255))
    prompt: Mapped[str] = mapped_column(Text)
    outline: Mapped[str] = mapped_column(Text, default="")
    word_limit: Mapped[int] = mapped_column(Integer, default=250)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")

    topic = relationship("Topic", back_populates="essays")


class PastPaper(Base):
    __tablename__ = "past_papers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exam_track_id: Mapped[int] = mapped_column(ForeignKey("exam_tracks.id"))
    topic_id: Mapped[int | None] = mapped_column(ForeignKey("topics.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    year: Mapped[str] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(Text, default="")

    exam_track = relationship("ExamTrack")
    topic = relationship("Topic", back_populates="past_papers")
    questions = relationship("PastPaperQuestion", back_populates="past_paper")


class PastPaperQuestion(Base):
    __tablename__ = "past_paper_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    past_paper_id: Mapped[int] = mapped_column(ForeignKey("past_papers.id"))
    text: Mapped[str] = mapped_column(Text)
    option_a: Mapped[str] = mapped_column(Text)
    option_b: Mapped[str] = mapped_column(Text)
    option_c: Mapped[str] = mapped_column(Text)
    option_d: Mapped[str] = mapped_column(Text)
    correct_option: Mapped[str] = mapped_column(String(1))
    explanation: Mapped[str] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    past_paper = relationship("PastPaper", back_populates="questions")


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    session_id: Mapped[int | None] = mapped_column(ForeignKey("quiz_sessions.id"), nullable=True)
    selected_option: Mapped[str] = mapped_column(String(1))
    is_correct: Mapped[bool] = mapped_column(Boolean)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="attempts")
    question = relationship("Question", back_populates="attempts")
    session = relationship("QuizSession", back_populates="attempts")


class TopicMastery(Base):
    __tablename__ = "topic_mastery"
    __table_args__ = (UniqueConstraint("user_id", "topic_id", name="uq_user_topic"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id"))
    attempts_count: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    mastery_score: Mapped[float] = mapped_column(Float, default=0.5)  # 0–1
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="topic_mastery")
    topic = relationship("Topic", back_populates="mastery_records")
