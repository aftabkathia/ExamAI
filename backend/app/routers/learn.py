from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.auth import CurrentUser
from app.database import get_db
from app.models import TopicNote, EssayPrompt, PastPaper, Topic
from app.schemas import (
    TopicNoteOut,
    EssayPromptOut,
    PastPaperOut,
    PastPaperListItem,
    PastPaperQuestionOut,
)

router = APIRouter(prefix="/learn", tags=["learn"])


def _note_out(note: TopicNote) -> TopicNoteOut:
    points = [p.strip() for p in (note.key_points or "").split("\n") if p.strip()]
    topic = note.topic
    exam_name = topic.exam_track.name if topic and topic.exam_track else None
    return TopicNoteOut(
        id=note.id,
        topic_id=note.topic_id,
        topic_name=topic.name if topic else None,
        exam_name=exam_name,
        title=note.title,
        summary=note.summary,
        content=note.content,
        key_points=points,
        order_index=note.order_index,
    )


@router.get("/notes", response_model=list[TopicNoteOut])
def list_notes(
    user: CurrentUser,
    exam_id: int | None = None,
    topic_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(TopicNote).options(
        joinedload(TopicNote.topic).joinedload(Topic.exam_track)
    )
    if topic_id:
        q = q.filter(TopicNote.topic_id == topic_id)
    elif exam_id:
        q = q.join(Topic).filter(Topic.exam_track_id == exam_id)
    notes = q.order_by(TopicNote.topic_id, TopicNote.order_index).all()
    return [_note_out(n) for n in notes]


@router.get("/notes/{note_id}", response_model=TopicNoteOut)
def get_note(note_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    note = (
        db.query(TopicNote)
        .options(joinedload(TopicNote.topic).joinedload(Topic.exam_track))
        .filter(TopicNote.id == note_id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return _note_out(note)


@router.get("/essays", response_model=list[EssayPromptOut])
def list_essays(
    user: CurrentUser,
    exam_id: int | None = None,
    topic_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(EssayPrompt).options(
        joinedload(EssayPrompt.topic).joinedload(Topic.exam_track)
    )
    if topic_id:
        q = q.filter(EssayPrompt.topic_id == topic_id)
    elif exam_id:
        q = q.join(Topic).filter(Topic.exam_track_id == exam_id)
    essays = q.order_by(EssayPrompt.topic_id).all()
    out = []
    for e in essays:
        out.append(
            EssayPromptOut(
                id=e.id,
                topic_id=e.topic_id,
                topic_name=e.topic.name if e.topic else None,
                exam_name=e.topic.exam_track.name if e.topic and e.topic.exam_track else None,
                title=e.title,
                prompt=e.prompt,
                outline=e.outline,
                word_limit=e.word_limit,
                difficulty=e.difficulty,
            )
        )
    return out


@router.get("/essays/{essay_id}", response_model=EssayPromptOut)
def get_essay(essay_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    e = (
        db.query(EssayPrompt)
        .options(joinedload(EssayPrompt.topic).joinedload(Topic.exam_track))
        .filter(EssayPrompt.id == essay_id)
        .first()
    )
    if not e:
        raise HTTPException(status_code=404, detail="Essay not found")
    return EssayPromptOut(
        id=e.id,
        topic_id=e.topic_id,
        topic_name=e.topic.name if e.topic else None,
        exam_name=e.topic.exam_track.name if e.topic and e.topic.exam_track else None,
        title=e.title,
        prompt=e.prompt,
        outline=e.outline,
        word_limit=e.word_limit,
        difficulty=e.difficulty,
    )


@router.get("/past-papers", response_model=list[PastPaperListItem])
def list_past_papers(
    user: CurrentUser,
    exam_id: int | None = None,
    topic_id: int | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(PastPaper).options(
        joinedload(PastPaper.exam_track),
        joinedload(PastPaper.topic),
        joinedload(PastPaper.questions),
    )
    if topic_id:
        q = q.filter(PastPaper.topic_id == topic_id)
    if exam_id:
        q = q.filter(PastPaper.exam_track_id == exam_id)
    papers = q.order_by(PastPaper.exam_track_id, PastPaper.year.desc()).all()
    return [
        PastPaperListItem(
            id=p.id,
            exam_track_id=p.exam_track_id,
            exam_name=p.exam_track.name if p.exam_track else None,
            topic_id=p.topic_id,
            topic_name=p.topic.name if p.topic else None,
            title=p.title,
            year=p.year,
            description=p.description,
            question_count=len(p.questions),
        )
        for p in papers
    ]


@router.get("/past-papers/{paper_id}", response_model=PastPaperOut)
def get_past_paper(paper_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    p = (
        db.query(PastPaper)
        .options(
            joinedload(PastPaper.exam_track),
            joinedload(PastPaper.topic),
            joinedload(PastPaper.questions),
        )
        .filter(PastPaper.id == paper_id)
        .first()
    )
    if not p:
        raise HTTPException(status_code=404, detail="Past paper not found")
    questions = sorted(p.questions, key=lambda x: x.order_index)
    return PastPaperOut(
        id=p.id,
        exam_track_id=p.exam_track_id,
        exam_name=p.exam_track.name if p.exam_track else None,
        topic_id=p.topic_id,
        topic_name=p.topic.name if p.topic else None,
        title=p.title,
        year=p.year,
        description=p.description,
        question_count=len(questions),
        questions=[PastPaperQuestionOut.model_validate(q) for q in questions],
    )
