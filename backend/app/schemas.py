from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = Field(min_length=2)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    credential: str


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    avatar_url: str | None = None
    current_streak: int = 0
    longest_streak: int = 0

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── Exams ─────────────────────────────────────────────────────────────────────

class TopicOut(BaseModel):
    id: int
    name: str
    description: str

    class Config:
        from_attributes = True


class ExamTrackOut(BaseModel):
    id: int
    code: str
    name: str
    category: str
    description: str
    icon: str
    topics: list[TopicOut] = []

    class Config:
        from_attributes = True


# ── Quiz ──────────────────────────────────────────────────────────────────────

class StartQuizRequest(BaseModel):
    exam_track_id: int
    total_questions: int = Field(default=10, ge=5, le=30)
    topic_id: int | None = None


class QuestionOut(BaseModel):
    id: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    difficulty: str
    topic_id: int
    topic_name: str | None = None
    source: str | None = None

    class Config:
        from_attributes = True


class QuizSessionOut(BaseModel):
    id: int
    exam_track_id: int
    total_questions: int
    correct_count: int
    completed: bool
    started_at: datetime

    class Config:
        from_attributes = True


class StartQuizResponse(BaseModel):
    session: QuizSessionOut
    question: QuestionOut


class SubmitAnswerRequest(BaseModel):
    session_id: int
    question_id: int
    selected_option: str
    time_spent_seconds: int = 0


class AnswerFeedback(BaseModel):
    is_correct: bool
    correct_option: str
    explanation: str
    selected_option: str
    mastery_score: float
    next_question: QuestionOut | None = None
    session_completed: bool = False
    session_score: int | None = None
    session_total: int | None = None


# ── Progress ──────────────────────────────────────────────────────────────────

class TopicProgress(BaseModel):
    topic_id: int
    topic_name: str
    exam_name: str
    attempts_count: int
    correct_count: int
    accuracy: float
    mastery_score: float


class DailyActivity(BaseModel):
    date: str
    attempts: int
    correct: int


class ProgressDashboard(BaseModel):
    total_attempts: int
    total_correct: int
    overall_accuracy: float
    current_streak: int
    longest_streak: int
    quizzes_completed: int
    topic_progress: list[TopicProgress]
    recent_activity: list[DailyActivity]
    weak_topics: list[TopicProgress]
    strong_topics: list[TopicProgress]


# ── Learning content ───────────────────────────────────────────────────────────

class TopicNoteOut(BaseModel):
    id: int
    topic_id: int
    topic_name: str | None = None
    exam_name: str | None = None
    title: str
    summary: str
    content: str
    key_points: list[str] = []
    order_index: int = 0

    class Config:
        from_attributes = True


class EssayPromptOut(BaseModel):
    id: int
    topic_id: int
    topic_name: str | None = None
    exam_name: str | None = None
    title: str
    prompt: str
    outline: str
    word_limit: int
    difficulty: str

    class Config:
        from_attributes = True


class PastPaperQuestionOut(BaseModel):
    id: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str
    explanation: str
    order_index: int = 0

    class Config:
        from_attributes = True


class PastPaperOut(BaseModel):
    id: int
    exam_track_id: int
    exam_name: str | None = None
    topic_id: int | None = None
    topic_name: str | None = None
    title: str
    year: str
    description: str
    question_count: int = 0
    questions: list[PastPaperQuestionOut] = []

    class Config:
        from_attributes = True


class PastPaperListItem(BaseModel):
    id: int
    exam_track_id: int
    exam_name: str | None = None
    topic_id: int | None = None
    topic_name: str | None = None
    title: str
    year: str
    description: str
    question_count: int = 0

    class Config:
        from_attributes = True
