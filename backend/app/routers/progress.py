from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.auth import CurrentUser
from app.database import get_db
from app.models import Attempt, QuizSession, TopicMastery, Topic
from app.schemas import ProgressDashboard, TopicProgress, DailyActivity

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/dashboard", response_model=ProgressDashboard)
def dashboard(user: CurrentUser, db: Session = Depends(get_db)):
    attempts = db.query(Attempt).filter(Attempt.user_id == user.id).all()
    total_attempts = len(attempts)
    total_correct = sum(1 for a in attempts if a.is_correct)
    overall_accuracy = (total_correct / total_attempts * 100) if total_attempts else 0.0

    quizzes_completed = (
        db.query(QuizSession)
        .filter(QuizSession.user_id == user.id, QuizSession.completed.is_(True))
        .count()
    )

    mastery_rows = (
        db.query(TopicMastery)
        .options(joinedload(TopicMastery.topic).joinedload(Topic.exam_track))
        .filter(TopicMastery.user_id == user.id)
        .all()
    )

    topic_progress: list[TopicProgress] = []
    for row in mastery_rows:
        accuracy = (row.correct_count / row.attempts_count * 100) if row.attempts_count else 0.0
        topic_progress.append(
            TopicProgress(
                topic_id=row.topic_id,
                topic_name=row.topic.name,
                exam_name=row.topic.exam_track.name if row.topic.exam_track else "",
                attempts_count=row.attempts_count,
                correct_count=row.correct_count,
                accuracy=round(accuracy, 1),
                mastery_score=round(row.mastery_score, 3),
            )
        )

    topic_progress.sort(key=lambda t: t.mastery_score)
    weak = [t for t in topic_progress if t.attempts_count > 0][:5]
    strong = sorted(
        [t for t in topic_progress if t.attempts_count >= 3],
        key=lambda t: t.mastery_score,
        reverse=True,
    )[:5]

    # Last 14 days activity
    since = datetime.utcnow() - timedelta(days=13)
    recent = [a for a in attempts if a.created_at >= since]
    by_day: dict[str, dict[str, int]] = defaultdict(lambda: {"attempts": 0, "correct": 0})
    for a in recent:
        key = a.created_at.strftime("%Y-%m-%d")
        by_day[key]["attempts"] += 1
        if a.is_correct:
            by_day[key]["correct"] += 1

    recent_activity: list[DailyActivity] = []
    for i in range(14):
        day = (datetime.utcnow() - timedelta(days=13 - i)).strftime("%Y-%m-%d")
        stats = by_day.get(day, {"attempts": 0, "correct": 0})
        recent_activity.append(
            DailyActivity(date=day, attempts=stats["attempts"], correct=stats["correct"])
        )

    return ProgressDashboard(
        total_attempts=total_attempts,
        total_correct=total_correct,
        overall_accuracy=round(overall_accuracy, 1),
        current_streak=user.current_streak,
        longest_streak=user.longest_streak,
        quizzes_completed=quizzes_completed,
        topic_progress=topic_progress,
        recent_activity=recent_activity,
        weak_topics=weak,
        strong_topics=strong,
    )
