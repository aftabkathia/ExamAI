"""AI Workspace API — notes, tasks, documents, whiteboard."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import CurrentUser
from app.database import get_db
from app.models import WorkspaceDocument, WorkspaceNote, WorkspaceTask
from app.services.workspace import get_or_create_whiteboard, workspace_summary

router = APIRouter(prefix="/workspace", tags=["workspace"])


class NoteIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=12000)


class NoteOut(NoteIn):
    id: int
    source: str
    created_at: str
    updated_at: str


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=4000)
    status: str = Field(default="todo", pattern="^(todo|doing|done)$")
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")


class TaskOut(TaskIn):
    id: int
    created_at: str
    updated_at: str


class DocumentMeta(BaseModel):
    id: int
    title: str
    filename: str
    mime: str
    source: str
    created_at: str


class DocumentFull(DocumentMeta):
    data_base64: str


class WhiteboardOut(BaseModel):
    id: int
    title: str
    canvas_data: str
    updated_at: str


class WhiteboardIn(BaseModel):
    title: str | None = None
    canvas_data: str = Field(max_length=500_000)


@router.get("/summary")
def summary(user: CurrentUser, db: Session = Depends(get_db)):
    return workspace_summary(db, user.id)


@router.get("/notes", response_model=list[NoteOut])
def list_notes(user: CurrentUser, db: Session = Depends(get_db)):
    rows = (
        db.query(WorkspaceNote)
        .filter(WorkspaceNote.user_id == user.id)
        .order_by(WorkspaceNote.updated_at.desc())
        .limit(100)
        .all()
    )
    return [
        NoteOut(
            id=r.id,
            title=r.title,
            content=r.content,
            source=r.source,
            created_at=r.created_at.isoformat(),
            updated_at=r.updated_at.isoformat() if r.updated_at else r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.post("/notes", response_model=NoteOut)
def create_note(payload: NoteIn, user: CurrentUser, db: Session = Depends(get_db)):
    note = WorkspaceNote(
        user_id=user.id,
        title=payload.title,
        content=payload.content,
        source="manual",
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return NoteOut(
        id=note.id,
        title=note.title,
        content=note.content,
        source=note.source,
        created_at=note.created_at.isoformat(),
        updated_at=note.updated_at.isoformat(),
    )


@router.patch("/notes/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int, payload: NoteIn, user: CurrentUser, db: Session = Depends(get_db)
):
    note = (
        db.query(WorkspaceNote)
        .filter(WorkspaceNote.id == note_id, WorkspaceNote.user_id == user.id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note.title = payload.title
    note.content = payload.content
    note.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(note)
    return NoteOut(
        id=note.id,
        title=note.title,
        content=note.content,
        source=note.source,
        created_at=note.created_at.isoformat(),
        updated_at=note.updated_at.isoformat(),
    )


@router.delete("/notes/{note_id}")
def delete_note(note_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    note = (
        db.query(WorkspaceNote)
        .filter(WorkspaceNote.id == note_id, WorkspaceNote.user_id == user.id)
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"ok": True}


@router.get("/tasks", response_model=list[TaskOut])
def list_tasks(user: CurrentUser, db: Session = Depends(get_db)):
    rows = (
        db.query(WorkspaceTask)
        .filter(WorkspaceTask.user_id == user.id)
        .order_by(WorkspaceTask.updated_at.desc())
        .limit(100)
        .all()
    )
    return [
        TaskOut(
            id=r.id,
            title=r.title,
            description=r.description,
            status=r.status,
            priority=r.priority,
            created_at=r.created_at.isoformat(),
            updated_at=r.updated_at.isoformat() if r.updated_at else r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.post("/tasks", response_model=TaskOut)
def create_task(payload: TaskIn, user: CurrentUser, db: Session = Depends(get_db)):
    task = WorkspaceTask(user_id=user.id, **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskOut(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )


@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int, payload: TaskIn, user: CurrentUser, db: Session = Depends(get_db)
):
    task = (
        db.query(WorkspaceTask)
        .filter(WorkspaceTask.id == task_id, WorkspaceTask.user_id == user.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for k, v in payload.model_dump().items():
        setattr(task, k, v)
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return TaskOut(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    task = (
        db.query(WorkspaceTask)
        .filter(WorkspaceTask.id == task_id, WorkspaceTask.user_id == user.id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"ok": True}


@router.get("/documents", response_model=list[DocumentMeta])
def list_documents(user: CurrentUser, db: Session = Depends(get_db)):
    rows = (
        db.query(WorkspaceDocument)
        .filter(WorkspaceDocument.user_id == user.id)
        .order_by(WorkspaceDocument.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        DocumentMeta(
            id=r.id,
            title=r.title,
            filename=r.filename,
            mime=r.mime,
            source=r.source,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.get("/documents/{doc_id}", response_model=DocumentFull)
def get_document(doc_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    doc = (
        db.query(WorkspaceDocument)
        .filter(WorkspaceDocument.id == doc_id, WorkspaceDocument.user_id == user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentFull(
        id=doc.id,
        title=doc.title,
        filename=doc.filename,
        mime=doc.mime,
        source=doc.source,
        created_at=doc.created_at.isoformat(),
        data_base64=doc.file_data,
    )


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    doc = (
        db.query(WorkspaceDocument)
        .filter(WorkspaceDocument.id == doc_id, WorkspaceDocument.user_id == user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    return {"ok": True}


@router.get("/whiteboard", response_model=WhiteboardOut)
def get_whiteboard(user: CurrentUser, db: Session = Depends(get_db)):
    board = get_or_create_whiteboard(db, user.id)
    return WhiteboardOut(
        id=board.id,
        title=board.title,
        canvas_data=board.canvas_data,
        updated_at=board.updated_at.isoformat() if board.updated_at else "",
    )


@router.put("/whiteboard", response_model=WhiteboardOut)
def save_whiteboard(
    payload: WhiteboardIn, user: CurrentUser, db: Session = Depends(get_db)
):
    board = get_or_create_whiteboard(db, user.id)
    board.canvas_data = payload.canvas_data
    if payload.title:
        board.title = payload.title[:255]
    board.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(board)
    return WhiteboardOut(
        id=board.id,
        title=board.title,
        canvas_data=board.canvas_data,
        updated_at=board.updated_at.isoformat(),
    )
