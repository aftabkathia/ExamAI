"""Adaptive mastery model — prioritizes weaker topics and adjusts difficulty."""

from __future__ import annotations

import random
from datetime import datetime, date, timedelta

from sqlalchemy.orm import Session

from app.models import Topic, TopicMastery, User


def get_or_create_mastery(db: Session, user_id: int, topic_id: int) -> TopicMastery:
    mastery = (
        db.query(TopicMastery)
        .filter(TopicMastery.user_id == user_id, TopicMastery.topic_id == topic_id)
        .first()
    )
    if not mastery:
        mastery = TopicMastery(user_id=user_id, topic_id=topic_id, mastery_score=0.5)
        db.add(mastery)
        db.commit()
        db.refresh(mastery)
    return mastery


def update_mastery(db: Session, user_id: int, topic_id: int, is_correct: bool) -> TopicMastery:
    """Exponential moving average of mastery: correct ↑, wrong ↓."""
    mastery = get_or_create_mastery(db, user_id, topic_id)
    mastery.attempts_count += 1
    if is_correct:
        mastery.correct_count += 1
        mastery.mastery_score = min(1.0, mastery.mastery_score + 0.08 * (1 - mastery.mastery_score))
    else:
        mastery.mastery_score = max(0.0, mastery.mastery_score - 0.12 * mastery.mastery_score - 0.05)
    mastery.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(mastery)
    return mastery


def select_topic(db: Session, user_id: int, topics: list[Topic], preferred_topic_id: int | None = None) -> Topic:
    """Weighted random selection favoring low mastery scores."""
    if preferred_topic_id:
        preferred = next((t for t in topics if t.id == preferred_topic_id), None)
        if preferred:
            return preferred

    if not topics:
        raise ValueError("No topics available")

    weights: list[float] = []
    for topic in topics:
        mastery = (
            db.query(TopicMastery)
            .filter(TopicMastery.user_id == user_id, TopicMastery.topic_id == topic.id)
            .first()
        )
        score = mastery.mastery_score if mastery else 0.5
        # Inverse mastery + exploration bonus for never-attempted
        weight = (1.0 - score) ** 2 + 0.15
        if not mastery or mastery.attempts_count == 0:
            weight += 0.25
        weights.append(max(weight, 0.05))

    return random.choices(topics, weights=weights, k=1)[0]


def recommend_difficulty(db: Session, user_id: int, topic_id: int) -> str:
    mastery = (
        db.query(TopicMastery)
        .filter(TopicMastery.user_id == user_id, TopicMastery.topic_id == topic_id)
        .first()
    )
    score = mastery.mastery_score if mastery else 0.5
    attempts = mastery.attempts_count if mastery else 0

    if attempts < 2:
        return "easy"
    if score < 0.4:
        return "easy"
    if score < 0.7:
        return "medium"
    return "hard"


def update_streak(db: Session, user: User) -> None:
    today = date.today()
    last = user.last_practice_date.date() if user.last_practice_date else None

    if last == today:
        return
    if last == today - timedelta(days=1):
        user.current_streak += 1
    else:
        user.current_streak = 1

    user.longest_streak = max(user.longest_streak, user.current_streak)
    user.last_practice_date = datetime.utcnow()
    db.commit()
