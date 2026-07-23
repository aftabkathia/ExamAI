from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import ExamTrack
from app.schemas import ExamTrackOut

router = APIRouter(prefix="/exams", tags=["exams"])


@router.get("", response_model=list[ExamTrackOut])
def list_exams(category: str | None = None, db: Session = Depends(get_db)):
    query = db.query(ExamTrack).options(joinedload(ExamTrack.topics))
    if category in {"academic", "government"}:
        query = query.filter(ExamTrack.category == category)
    tracks = query.order_by(ExamTrack.category, ExamTrack.name).all()
    return tracks


@router.get("/{exam_id}", response_model=ExamTrackOut)
def get_exam(exam_id: int, db: Session = Depends(get_db)):
    track = (
        db.query(ExamTrack)
        .options(joinedload(ExamTrack.topics))
        .filter(ExamTrack.id == exam_id)
        .first()
    )
    if not track:
        raise HTTPException(status_code=404, detail="Exam not found")
    return track
