from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.auth import CurrentUser
from app.database import get_db
from app.models import ExamTrack, Question, QuizSession, Attempt, Topic
from app.schemas import (
    StartQuizRequest,
    StartQuizResponse,
    QuizSessionOut,
    QuestionOut,
    SubmitAnswerRequest,
    AnswerFeedback,
)
from app.services.adaptive import (
    select_topic,
    recommend_difficulty,
    update_mastery,
    update_streak,
)
from app.services.groq_service import generate_mcq

router = APIRouter(prefix="/quiz", tags=["quiz"])


def _question_out(question: Question, topic_name: str | None = None) -> QuestionOut:
    return QuestionOut(
        id=question.id,
        text=question.text,
        option_a=question.option_a,
        option_b=question.option_b,
        option_c=question.option_c,
        option_d=question.option_d,
        difficulty=question.difficulty,
        topic_id=question.topic_id,
        topic_name=topic_name,
        source=getattr(question, "source", None),
    )


def _all_session_question_texts(db: Session, session_id: int, user_id: int) -> set[str]:
    """Exclude every question already shown in this quiz session."""
    attempt_q = (
        db.query(Question.text)
        .join(Attempt, Attempt.question_id == Question.id)
        .filter(Attempt.session_id == session_id)
        .all()
    )
    texts = {t[0] for t in attempt_q}
    session = db.get(QuizSession, session_id)
    if session:
        recent = (
            db.query(Question.text)
            .join(Topic, Topic.id == Question.topic_id)
            .filter(
                Topic.exam_track_id == session.exam_track_id,
                Question.created_at >= session.started_at,
            )
            .all()
        )
        texts |= {t[0] for t in recent}
    return texts


def _create_adaptive_question(
    db: Session,
    user_id: int,
    exam: ExamTrack,
    topics: list[Topic],
    preferred_topic_id: int | None = None,
    exclude_texts: set[str] | None = None,
) -> Question:
    from app.models import TopicMastery

    topic = select_topic(db, user_id, topics, preferred_topic_id)
    difficulty = recommend_difficulty(db, user_id, topic.id)
    m = (
        db.query(TopicMastery)
        .filter(TopicMastery.user_id == user_id, TopicMastery.topic_id == topic.id)
        .first()
    )
    weak_focus = m is None or m.mastery_score < 0.45

    data = generate_mcq(
        exam_name=exam.name,
        topic_name=topic.name,
        difficulty=difficulty,
        weak_focus=weak_focus,
        exclude_texts=exclude_texts or set(),
    )
    question = Question(
        topic_id=topic.id,
        text=data["text"],
        option_a=data["option_a"],
        option_b=data["option_b"],
        option_c=data["option_c"],
        option_d=data["option_d"],
        correct_option=data["correct_option"],
        explanation=data["explanation"],
        difficulty=data["difficulty"],
        source=data.get("source", "bank"),
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.post("/start", response_model=StartQuizResponse)
def start_quiz(payload: StartQuizRequest, user: CurrentUser, db: Session = Depends(get_db)):
    exam = (
        db.query(ExamTrack)
        .options(joinedload(ExamTrack.topics))
        .filter(ExamTrack.id == payload.exam_track_id)
        .first()
    )
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    if not exam.topics:
        raise HTTPException(status_code=400, detail="Exam has no topics")

    session = QuizSession(
        user_id=user.id,
        exam_track_id=exam.id,
        preferred_topic_id=payload.topic_id,
        total_questions=payload.total_questions,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    question = _create_adaptive_question(
        db, user.id, exam, exam.topics, payload.topic_id, exclude_texts=set()
    )
    topic = db.get(Topic, question.topic_id)

    return StartQuizResponse(
        session=QuizSessionOut.model_validate(session),
        question=_question_out(question, topic.name if topic else None),
    )


@router.post("/answer", response_model=AnswerFeedback)
def submit_answer(payload: SubmitAnswerRequest, user: CurrentUser, db: Session = Depends(get_db)):
    session = db.get(QuizSession, payload.session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.completed:
        raise HTTPException(status_code=400, detail="Quiz already completed")

    question = db.get(Question, payload.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    selected = payload.selected_option.strip().upper()
    if selected not in {"A", "B", "C", "D"}:
        raise HTTPException(status_code=400, detail="Invalid option")

    is_correct = selected == question.correct_option
    attempt = Attempt(
        user_id=user.id,
        question_id=question.id,
        session_id=session.id,
        selected_option=selected,
        is_correct=is_correct,
        time_spent_seconds=max(0, payload.time_spent_seconds),
    )
    db.add(attempt)

    if is_correct:
        session.correct_count += 1

    mastery = update_mastery(db, user.id, question.topic_id, is_correct)
    update_streak(db, user)

    answered = db.query(Attempt).filter(Attempt.session_id == session.id).count()
    session_completed = answered >= session.total_questions
    next_q_out = None

    if session_completed:
        session.completed = True
        session.completed_at = datetime.utcnow()
        db.commit()
    else:
        exam = (
            db.query(ExamTrack)
            .options(joinedload(ExamTrack.topics))
            .filter(ExamTrack.id == session.exam_track_id)
            .first()
        )
        exclude = _all_session_question_texts(db, session.id, user.id)
        exclude.add(question.text)
        next_question = _create_adaptive_question(
            db,
            user.id,
            exam,
            exam.topics,
            preferred_topic_id=session.preferred_topic_id,
            exclude_texts=exclude,
        )
        topic = db.get(Topic, next_question.topic_id)
        next_q_out = _question_out(next_question, topic.name if topic else None)
        db.commit()

    return AnswerFeedback(
        is_correct=is_correct,
        correct_option=question.correct_option,
        explanation=question.explanation,
        selected_option=selected,
        mastery_score=round(mastery.mastery_score, 3),
        next_question=next_q_out,
        session_completed=session_completed,
        session_score=session.correct_count if session_completed else None,
        session_total=session.total_questions if session_completed else None,
    )


@router.get("/session/{session_id}", response_model=QuizSessionOut)
def get_session(session_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    session = db.get(QuizSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return QuizSessionOut.model_validate(session)
