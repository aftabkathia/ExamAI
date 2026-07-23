"""Personal memory — per-user preferences, projects, goals, and chat history."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from groq import Groq
from sqlalchemy.orm import Session

from app.models import ChatMessage, UserMemory

TEXT_MODEL = "llama-3.3-70b-versatile"
MAX_STORED_MESSAGES = 200
MAX_CONTEXT_MESSAGES = 24
MAX_MEMORIES_IN_PROMPT = 14

_EXTRACT_SYSTEM = """You extract durable personal facts from a chat turn to remember later.
Categories:
- preference: language, style, how user likes answers
- project: ongoing work (websites, apps, assignments, business ideas)
- goal: exams, career, learning targets
- fact: stable personal info (city, field of study, job)

Return JSON only:
{"memories":[{"category":"project","title":"Portfolio website","content":"Building Next.js portfolio; hero section in progress; dark theme"}]}

Rules:
- Max 3 new items per turn
- Only long-term useful facts — not one-off trivia
- Update existing topics with richer detail when mentioned again
- Empty array if nothing worth saving"""


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9\u0600-\u06FF]{3,}", (text or "").lower())
    stop = {
        "the", "and", "for", "what", "who", "when", "where", "which", "how",
        "about", "from", "with", "that", "this", "have", "has", "was", "were",
        "are", "is", "can", "you", "please", "tell", "give", "explain", "main",
        "kya", "hai", "mera", "mere", "your", "continue", "yesterday",
    }
    return {w for w in words if w not in stop}


def get_persisted_history(db: Session, user_id: int, limit: int = MAX_CONTEXT_MESSAGES) -> list[dict[str, str]]:
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return [{"role": r.role, "content": r.content} for r in reversed(rows)]


def retrieve_memories(db: Session, user_id: int, query: str, limit: int = MAX_MEMORIES_IN_PROMPT) -> list[UserMemory]:
    all_mem = (
        db.query(UserMemory)
        .filter(UserMemory.user_id == user_id)
        .order_by(UserMemory.updated_at.desc())
        .limit(80)
        .all()
    )
    if not all_mem:
        return []

    qtokens = _tokens(query)
    scored: list[tuple[int, UserMemory]] = []
    for mem in all_mem:
        blob = f"{mem.category} {mem.title} {mem.content}".lower()
        score = sum(2 if t in mem.title.lower() else 1 for t in qtokens if t in blob)
        if mem.category == "project":
            score += 1
        scored.append((score, mem))

    scored.sort(key=lambda x: (x[0], x[1].updated_at), reverse=True)
    picked: list[UserMemory] = []
    seen_titles: set[str] = set()
    for score, mem in scored:
        if score <= 0 and len(picked) >= 5:
            continue
        key = mem.title.lower()
        if key in seen_titles:
            continue
        seen_titles.add(key)
        picked.append(mem)
        if len(picked) >= limit:
            break

    if len(picked) < 5:
        for mem in all_mem:
            if mem.title.lower() not in seen_titles:
                picked.append(mem)
                seen_titles.add(mem.title.lower())
            if len(picked) >= limit:
                break
    return picked[:limit]


def format_memory_block(memories: list[UserMemory], recent_snippet: str = "") -> str:
    if not memories and not recent_snippet:
        return ""

    lines = [
        "\n\n## USER PERSONAL MEMORY (remember and use this — do NOT ask user to repeat)",
        "This student has talked to you before. Use their preferences, projects, and goals.",
    ]
    by_cat: dict[str, list[UserMemory]] = {}
    for m in memories:
        by_cat.setdefault(m.category, []).append(m)

    labels = {
        "preference": "Preferences",
        "project": "Active projects",
        "goal": "Goals",
        "fact": "Personal facts",
    }
    for cat, label in labels.items():
        items = by_cat.get(cat, [])
        if not items:
            continue
        lines.append(f"\n### {label}")
        for item in items:
            lines.append(f"- **{item.title}:** {item.content}")

    if recent_snippet:
        lines.append(f"\n### Recent context snippet\n{recent_snippet[:1200]}")

    lines.append(
        "\nIf they say 'continue', 'yesterday', 'we were building', etc. — pick up from memory above."
    )
    return "\n".join(lines)


def build_memory_context(db: Session, user_id: int, query: str) -> str:
    memories = retrieve_memories(db, user_id, query)
    recent = get_persisted_history(db, user_id, limit=6)
    snippet = ""
    if recent:
        parts = [f"{m['role']}: {m['content'][:200]}" for m in recent[-4:]]
        snippet = "\n".join(parts)
    return format_memory_block(memories, snippet)


def save_message(db: Session, user_id: int, role: str, content: str) -> None:
    text = (content or "").strip()
    if not text or role not in {"user", "assistant"}:
        return
    db.add(ChatMessage(user_id=user_id, role=role, content=text[:12000]))
    db.commit()
    _trim_old_messages(db, user_id)


def _trim_old_messages(db: Session, user_id: int) -> None:
    count = db.query(ChatMessage).filter(ChatMessage.user_id == user_id).count()
    if count <= MAX_STORED_MESSAGES:
        return
    to_delete = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(count - MAX_STORED_MESSAGES)
        .all()
    )
    for row in to_delete:
        db.delete(row)
    db.commit()


def upsert_memory(db: Session, user_id: int, category: str, title: str, content: str) -> None:
    category = category if category in {"preference", "project", "goal", "fact"} else "fact"
    title = title.strip()[:255]
    content = content.strip()[:4000]
    if not title or not content:
        return

    existing = (
        db.query(UserMemory)
        .filter(UserMemory.user_id == user_id, UserMemory.title == title)
        .first()
    )
    if existing:
        existing.category = category
        existing.content = content
        existing.updated_at = datetime.utcnow()
    else:
        db.add(
            UserMemory(
                user_id=user_id,
                category=category,
                title=title,
                content=content,
            )
        )
    db.commit()


def _parse_json(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE)
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    return json.loads(text)


def extract_memories_from_turn(
    client: Groq,
    user_message: str,
    assistant_reply: str,
    existing_titles: list[str],
) -> list[dict[str, str]]:
    if not user_message.strip():
        return []
    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[
                {"role": "system", "content": _EXTRACT_SYSTEM},
                {
                    "role": "user",
                    "content": (
                        f"Existing memory titles: {', '.join(existing_titles[:20]) or 'none'}\n\n"
                        f"USER: {user_message[:2000]}\n\n"
                        f"ASSISTANT: {assistant_reply[:2000]}"
                    ),
                },
            ],
            temperature=0.2,
            max_tokens=500,
            response_format={"type": "json_object"},
        )
        data = _parse_json(response.choices[0].message.content or "{}")
        items = data.get("memories") or []
        out: list[dict[str, str]] = []
        for item in items[:3]:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title", "")).strip()
            content = str(item.get("content", "")).strip()
            category = str(item.get("category", "fact")).strip()
            if title and content:
                out.append({"category": category, "title": title, "content": content})
        return out
    except Exception:
        return []


def persist_turn(
    db: Session,
    user_id: int,
    user_message: str,
    assistant_reply: str,
    groq_client: Groq | None = None,
) -> None:
    """Save chat turn and extract long-term memories + workspace items."""
    save_message(db, user_id, "user", user_message)
    save_message(db, user_id, "assistant", assistant_reply)

    if not groq_client or not user_message.strip():
        return

    from app.services.workspace import sync_from_conversation

    existing = (
        db.query(UserMemory.title)
        .filter(UserMemory.user_id == user_id)
        .all()
    )
    titles = [t[0] for t in existing]
    for item in extract_memories_from_turn(
        groq_client, user_message, assistant_reply, titles
    ):
        upsert_memory(db, user_id, item["category"], item["title"], item["content"])

    sync_from_conversation(db, user_id, user_message, assistant_reply, groq_client)


def list_memories(db: Session, user_id: int) -> list[dict[str, Any]]:
    rows = (
        db.query(UserMemory)
        .filter(UserMemory.user_id == user_id)
        .order_by(UserMemory.updated_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": r.id,
            "category": r.category,
            "title": r.title,
            "content": r.content,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in rows
    ]
