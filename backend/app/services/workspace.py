"""AI Workspace — connected notes, tasks, documents, whiteboard."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from groq import Groq
from sqlalchemy.orm import Session

from app.models import (
    WorkspaceDocument,
    WorkspaceNote,
    WorkspaceTask,
    WorkspaceWhiteboard,
)

TEXT_MODEL = "llama-3.3-70b-versatile"

_SYNC_SYSTEM = """From this chat turn, extract items for the user's AI workspace.
Return JSON only:
{
  "notes": [{"title": "short title", "content": "note body"}],
  "tasks": [{"title": "task title", "description": "optional detail", "priority": "low|medium|high"}]
}
Rules:
- Max 2 notes and 2 tasks per turn
- Only when user clearly wants to save, remember, plan, or track something
- "add task", "remind me", "note this", "save this", study plans → extract
- Empty arrays if nothing to save"""


def build_workspace_context(db: Session, user_id: int) -> str:
    notes = (
        db.query(WorkspaceNote)
        .filter(WorkspaceNote.user_id == user_id)
        .order_by(WorkspaceNote.updated_at.desc())
        .limit(6)
        .all()
    )
    tasks = (
        db.query(WorkspaceTask)
        .filter(WorkspaceTask.user_id == user_id, WorkspaceTask.status != "done")
        .order_by(WorkspaceTask.updated_at.desc())
        .limit(10)
        .all()
    )
    docs = (
        db.query(WorkspaceDocument)
        .filter(WorkspaceDocument.user_id == user_id)
        .order_by(WorkspaceDocument.created_at.desc())
        .limit(5)
        .all()
    )
    if not notes and not tasks and not docs:
        return ""

    lines = [
        "\n\n## AI WORKSPACE (connected — reference these; user sees same data in Notes/Tasks/Documents tabs)",
    ]
    if notes:
        lines.append("\n### Workspace notes")
        for n in notes:
            lines.append(f"- **{n.title}:** {n.content[:300]}")
    if tasks:
        lines.append("\n### Open tasks")
        for t in tasks:
            lines.append(f"- [{t.status}] **{t.title}** ({t.priority}) — {t.description[:200]}")
    if docs:
        lines.append("\n### Workspace documents")
        for d in docs:
            lines.append(f"- **{d.title}** ({d.filename})")
    lines.append("\nUser can say 'check my tasks', 'open my notes on X', 'continue whiteboard ideas'.")
    return "\n".join(lines)


def save_document(
    db: Session,
    user_id: int,
    title: str,
    filename: str,
    mime: str,
    data_base64: str,
    source: str = "generated",
) -> WorkspaceDocument:
    doc = WorkspaceDocument(
        user_id=user_id,
        title=title[:255],
        filename=filename[:255],
        mime=mime,
        file_data=data_base64,
        source=source,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _parse_json(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def sync_from_conversation(
    db: Session,
    user_id: int,
    user_message: str,
    assistant_reply: str,
    client: Groq | None,
) -> None:
    if not client or not user_message.strip():
        return
    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": _SYNC_SYSTEM},
                {
                    "role": "user",
                    "content": f"USER: {user_message[:2000]}\n\nASSISTANT: {assistant_reply[:2000]}",
                },
            ],
            temperature=0.2,
            max_tokens=600,
            response_format={"type": "json_object"},
        )
        data = _parse_json(response.choices[0].message.content or "{}")
    except Exception:
        return

    for note in (data.get("notes") or [])[:2]:
        if not isinstance(note, dict):
            continue
        title = str(note.get("title", "")).strip()
        content = str(note.get("content", "")).strip()
        if title and content:
            db.add(
                WorkspaceNote(
                    user_id=user_id,
                    title=title[:255],
                    content=content[:8000],
                    source="chat",
                )
            )

    for task in (data.get("tasks") or [])[:2]:
        if not isinstance(task, dict):
            continue
        title = str(task.get("title", "")).strip()
        if not title:
            continue
        priority = str(task.get("priority", "medium"))
        if priority not in {"low", "medium", "high"}:
            priority = "medium"
        db.add(
            WorkspaceTask(
                user_id=user_id,
                title=title[:255],
                description=str(task.get("description", ""))[:4000],
                status="todo",
                priority=priority,
            )
        )
    db.commit()


def workspace_summary(db: Session, user_id: int) -> dict[str, Any]:
    from app.models import IntelDocument

    return {
        "notes_count": db.query(WorkspaceNote).filter(WorkspaceNote.user_id == user_id).count(),
        "tasks_open": db.query(WorkspaceTask)
        .filter(WorkspaceTask.user_id == user_id, WorkspaceTask.status != "done")
        .count(),
        "documents_count": db.query(WorkspaceDocument)
        .filter(WorkspaceDocument.user_id == user_id)
        .count(),
        "intel_documents": db.query(IntelDocument)
        .filter(IntelDocument.user_id == user_id)
        .count(),
        "has_whiteboard": db.query(WorkspaceWhiteboard)
        .filter(WorkspaceWhiteboard.user_id == user_id)
        .first()
        is not None,
    }


def get_or_create_whiteboard(db: Session, user_id: int) -> WorkspaceWhiteboard:
    board = (
        db.query(WorkspaceWhiteboard)
        .filter(WorkspaceWhiteboard.user_id == user_id)
        .first()
    )
    if not board:
        board = WorkspaceWhiteboard(user_id=user_id, canvas_data="[]")
        db.add(board)
        db.commit()
        db.refresh(board)
    return board
