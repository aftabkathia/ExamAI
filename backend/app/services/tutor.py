"""ExamAI Tutor — grounded chatbot for Pakistani competitive exams."""

from __future__ import annotations

import re
from typing import Any

from groq import Groq
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.models import TopicNote, EssayPrompt, PastPaperQuestion
from app.services.question_bank import BANK

settings = get_settings()

SYSTEM_PROMPT = """You are **ExamAI Assistant** — a knowledgeable, friendly AI that helps with **everything**, not only exams.

You are especially strong on Pakistani competitive exams (CSS, MDCAT, ECAT, NET, NTS, PPSC, FPSC, OTS) but you also answer general questions: daily life, technology, health basics, careers, culture, news frameworks, creative writing, coding, and more.

## Languages (CRITICAL)
- Understand and reply in **English**, **Urdu** (اردو), **Roman Urdu** (Latin script: "aap kaisay hain", "yeh kya hai"), **Punjabi-style Roman**, **Hindi**, and other languages when the user writes in them.
- **Match the user's language**: Roman Urdu question → Roman Urdu answer (unless they ask for English).
- Urdu script question → Urdu script answer when natural.
- Mixed language is fine (Urdu + English code-switching).

## Personal memory
- You remember this user's **preferences, projects, goals**, and **past conversations** (see USER PERSONAL MEMORY when provided).
- If they say "continue", "yesterday", "we were building", or refer to prior work — use memory; never ask them to repeat everything.
- History (world, subcontinent, Pakistan) · Science · Maths · Computer · English · Islamiat
- Pakistan Affairs · Current Affairs · IQ/Reasoning · Essays
- General knowledge, how-to, advice, tech, health (non-medical-diagnosis), culture, religion (respectful)
- PDF/image analysis · Voice-friendly concise answers when user spoke

## Answer style
1. Be **accurate** and helpful. Use KNOWLEDGE CONTEXT when provided.
2. MCQs: state answer, explain why, rule out distractors.
3. Maths: show steps. History: dates + significance.
4. Keep answers clear — bullets or short paragraphs. For voice replies, prefer slightly shorter, spoken-friendly sentences.
5. If unsure, say so honestly — never invent citations.
6. PDFs: read extract, summarise, answer from content, make MCQs if asked.
7. **Uploaded images:** describe, read text, and solve/explain what you see.
8. **Image creation:** when the user asks to draw/create/generate an image or diagram, the system generates it automatically.
9. **Document creation:** you CAN create PDF, Word, Excel, and PowerPoint files when asked.
10. **AI Workspace:** Chat, Notes, Tasks, Documents, Doc Intel, and Whiteboard are connected.
11. **Document Intelligence:** User can upload hundreds of PDFs (invoices, contracts) and search them — answer from their library when they ask find/search/which documents questions.
12. You are ExamAI's built-in assistant (Groq LLM + local knowledge), not a separate human tutor.
"""

VISION_MODELS = [
    "qwen/qwen3.6-27b",  # Groq vision model (2026)
]
TEXT_MODEL = "llama-3.3-70b-versatile"

IMAGE_ANALYSIS_PROMPT = """The user uploaded an image and wants you to **see and explain it**.

You MUST:
1. Look at the image carefully — read any text, numbers, diagrams, MCQs, handwriting, charts, or photos.
2. Describe what you see in clear detail.
3. If it is a question/MCQ, solve it and explain step-by-step.
4. If it is notes or a diagram, summarise and teach the key points.
5. Match the user's language (English / Urdu / Roman Urdu).

Answer directly in your final response. Do NOT say you cannot see the image — you have the image in this message."""

def _clean_model_reply(text: str) -> str:
    """Remove Qwen-style thinking blocks; return the user-facing answer."""
    cleaned = (text or "").strip()
    cleaned = re.sub(
        r"<think>.*?</think>\s*",
        "",
        cleaned,
        flags=re.DOTALL | re.IGNORECASE,
    )
    cleaned = cleaned.strip()
    return cleaned or (text or "").strip()


def _groq_completion(
    client: Groq,
    model: str,
    messages: list[dict[str, Any]],
    max_tokens: int = 1600,
) -> str:
    """Call Groq chat with compatible token param."""
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
    }
    # Newer Groq models prefer max_completion_tokens
    if "qwen" in model or "llama-4" in model:
        kwargs["max_completion_tokens"] = max_tokens
    else:
        kwargs["max_tokens"] = max_tokens
    response = client.chat.completions.create(**kwargs)
    return _clean_model_reply(response.choices[0].message.content or "")


def _vision_messages(
    system: str,
    prompt_text: str,
    images: list[dict[str, str]],
    history: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Build messages for vision — instructions + image in one user turn."""
    instruction = (
        f"{IMAGE_ANALYSIS_PROMPT}\n\n"
        f"--- Background ---\n{system[:4000]}\n\n"
        f"--- User request ---\n{prompt_text}"
    )
    content_parts: list[dict[str, Any]] = [{"type": "text", "text": instruction}]
    for img in images[:3]:
        content_parts.append(
            {"type": "image_url", "image_url": {"url": img["data_url"]}}
        )

    msgs: list[dict[str, Any]] = []
    # Short text-only history (vision models handle limited multi-turn)
    for m in history[-4:]:
        if m.get("role") in {"user", "assistant"} and m.get("content"):
            msgs.append({"role": m["role"], "content": m["content"][:2000]})
    msgs.append({"role": "user", "content": content_parts})
    return msgs


def _try_vision(client: Groq, messages: list[dict[str, Any]]) -> tuple[str, str]:
    """Try vision models in order; return (reply, model_used)."""
    last_err: Exception | None = None
    for model in VISION_MODELS:
        try:
            reply = _groq_completion(client, model, messages, max_tokens=1800)
            if reply:
                return reply, model
        except Exception as exc:
            last_err = exc
            continue
    raise last_err or RuntimeError("All vision models failed")


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9\u0600-\u06FF]{3,}", text.lower())
    stop = {
        "the", "and", "for", "what", "who", "when", "where", "which", "how",
        "about", "from", "with", "that", "this", "have", "has", "was", "were",
        "are", "is", "can", "you", "please", "tell", "give", "explain",
    }
    return {w for w in words if w not in stop}


def retrieve_knowledge(db: Session, query: str, limit: int = 6) -> str:
    """Lightweight keyword retrieval over notes, essays, bank, and past papers."""
    qtokens = _tokens(query)
    if not qtokens:
        qtokens = set(query.lower().split())

    chunks: list[tuple[int, str]] = []

    # Notes
    notes = (
        db.query(TopicNote)
        .options(joinedload(TopicNote.topic))
        .all()
    )
    for note in notes:
        blob = f"{note.title} {note.summary} {note.content} {note.key_points} {note.topic.name if note.topic else ''}".lower()
        score = sum(1 for t in qtokens if t in blob)
        if score:
            topic = note.topic.name if note.topic else "General"
            body = note.content[:900]
            chunks.append((score + 2, f"[NOTE:{topic}] {note.title}\n{note.summary}\n{body}"))

    # Essay outlines (for writing questions)
    if any(t in query.lower() for t in ("essay", "outline", "write", "composition")):
        essays = db.query(EssayPrompt).options(joinedload(EssayPrompt.topic)).limit(40).all()
        for e in essays:
            blob = f"{e.title} {e.prompt} {e.outline}".lower()
            score = sum(1 for t in qtokens if t in blob)
            if score:
                chunks.append((score + 1, f"[ESSAY] {e.title}\nPrompt: {e.prompt}\nOutline:\n{e.outline}"))

    # Question bank facts
    for topic_key, questions in BANK.items():
        for q in questions:
            blob = f"{q['text']} {q['option_a']} {q['option_b']} {q['option_c']} {q['option_d']} {q['explanation']} {topic_key}".lower()
            score = sum(1 for t in qtokens if t in blob)
            if score >= 2 or (score >= 1 and len(qtokens) <= 3):
                ans = {"A": q["option_a"], "B": q["option_b"], "C": q["option_c"], "D": q["option_d"]}[
                    q["correct_option"]
                ]
                chunks.append(
                    (
                        score + 3,
                        f"[MCQ:{topic_key}] Q: {q['text']}\nCorrect: {q['correct_option']}) {ans}\nWhy: {q['explanation']}",
                    )
                )

    # Past paper explanations in DB
    try:
        ppqs = db.query(PastPaperQuestion).limit(400).all()
        for q in ppqs:
            blob = f"{q.text} {q.explanation}".lower()
            score = sum(1 for t in qtokens if t in blob)
            if score >= 2:
                ans = {"A": q.option_a, "B": q.option_b, "C": q.option_c, "D": q.option_d}.get(
                    q.correct_option, ""
                )
                chunks.append(
                    (
                        score + 2,
                        f"[PAST PAPER] Q: {q.text}\nCorrect: {q.correct_option}) {ans}\nWhy: {q.explanation}",
                    )
                )
    except Exception:
        pass

    chunks.sort(key=lambda x: x[0], reverse=True)
    top = [c[1] for c in chunks[:limit]]
    if not top:
        return "No specific local snippet matched. Use your trained exam knowledge carefully and state uncertainty if needed."
    return "\n\n---\n\n".join(top)


def _offline_answer(query: str, context: str) -> str:
    """Deterministic fallback when Groq is unavailable — use best MCQ/note hit."""
    if context and "[MCQ:" in context:
        first = context.split("---")[0].strip()
        return (
            f"**From ExamAI knowledge base:**\n\n{first}\n\n"
            "_Tip: Add/refresh GROQ_API_KEY for fuller conversational tutoring._"
        )
    if context and "[NOTE:" in context:
        first = context.split("---")[0].strip()
        return (
            f"**Revision note match:**\n\n{first}\n\n"
            "Ask a more specific question (e.g. a date, formula, or MCQ) for a sharper answer."
        )
    return (
        "I couldn't reach the live AI model right now. "
        "Try again shortly, or study **Notes** / **Past Papers** on ExamAI. "
        "Make sure `GROQ_API_KEY` is set in the backend `.env`."
    )


def chat_completion(
    db: Session,
    messages: list[dict[str, str]],
    user_message: str,
    pdf_sections: list[dict[str, str]] | None = None,
    images: list[dict[str, str]] | None = None,
    user_id: int | None = None,
) -> dict[str, Any]:
    """Generate a tutor reply with retrieved ExamAI knowledge + optional PDF/images."""
    from app.config import get_settings as _gs

    _gs.cache_clear()
    cfg = _gs()

    pdf_sections = pdf_sections or []
    images = images or []

    query_for_retrieval = user_message
    if pdf_sections and not query_for_retrieval.strip():
        query_for_retrieval = pdf_sections[0]["text"][:500]
    context = retrieve_knowledge(db, query_for_retrieval or "exam preparation")

    memory_block = ""
    if user_id:
        from app.services.user_memory import build_memory_context, get_persisted_history
        from app.services.workspace import build_workspace_context

        memory_block = build_memory_context(db, user_id, query_for_retrieval or user_message)
        memory_block += build_workspace_context(db, user_id)
        from app.services.document_intelligence import build_intel_context_summary

        memory_block += build_intel_context_summary(db, user_id)
        persisted = get_persisted_history(db, user_id)
        if persisted:
            history = persisted
        else:
            history = messages[-10:]
    else:
        history = messages[-10:]

    upload_block = ""
    if pdf_sections:
        parts = []
        for p in pdf_sections:
            parts.append(f"### Uploaded PDF: {p['name']}\n{p['text']}")
        upload_block += (
            "\n\n## UPLOADED PDF CONTENT\n"
            "The student attached these PDFs. Prefer this content when answering.\n\n"
            + "\n\n".join(parts)
        )
    if images:
        names = ", ".join(img["name"] for img in images)
        upload_block += (
            f"\n\n## UPLOADED IMAGES\n"
            f"The student attached image(s): {names}. "
            "Inspect the image(s) carefully (notes, MCQs, diagrams, handwriting) and answer accordingly."
        )

    system = (
        SYSTEM_PROMPT
        + memory_block
        + "\n\n## KNOWLEDGE CONTEXT (from ExamAI notes, past papers, MCQ bank)\n"
        + context
        + upload_block
        + "\n\nUse this context when relevant. If context conflicts with a well-known fact, prefer the more reliable exam-standard fact and explain briefly."
    )

    prompt_text = user_message.strip() or (
        "Please analyse my uploaded file(s). Summarise the important exam points and explain anything that looks like a question."
        if (pdf_sections or images)
        else "Hello"
    )

    api_messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
    for m in history:
        role = m.get("role", "user")
        if role not in {"user", "assistant"}:
            continue
        content = (m.get("content") or "").strip()
        if content:
            api_messages.append({"role": role, "content": content})

    if not cfg.groq_api_key or cfg.groq_api_key.startswith("your_"):
        if pdf_sections:
            preview = pdf_sections[0]["text"][:1200]
            reply = (
                f"**PDF received ({pdf_sections[0]['name']}).** Live AI is offline, so here is a text extract preview:\n\n"
                f"{preview}\n\n_Set GROQ_API_KEY for full tutoring on this PDF._"
            )
            return {"reply": reply, "grounded": True, "model": "offline-kb"}
        if images:
            return {
                "reply": (
                    "Image received, but live AI is offline. "
                    "Set `GROQ_API_KEY` in backend `.env` and restart the server to enable image explanation."
                ),
                "grounded": False,
                "model": "offline-kb",
            }
        reply = _offline_answer(prompt_text, context)
        return {"reply": reply, "grounded": True, "model": "offline-kb"}

    try:
        client = Groq(api_key=cfg.groq_api_key)

        if not images and not pdf_sections:
            from app.services.document_generation import (
                generate_document_from_message,
                wants_document_generation,
            )
            from app.services.document_intelligence import (
                ask_documents,
                wants_doc_intel_query,
            )
            from app.services.image_generation import (
                generate_image_from_message,
                wants_image_generation,
            )

            if user_id and wants_doc_intel_query(prompt_text):
                try:
                    result = ask_documents(db, user_id, prompt_text, client)
                    return {
                        "reply": result["answer"],
                        "grounded": True,
                        "model": "doc-intel",
                        "sources": result.get("sources", []),
                    }
                except Exception as exc:
                    return {
                        "reply": (
                            "Document search failed. Check your **Doc Intel** library has PDFs uploaded.\n\n"
                            f"_Detail: {type(exc).__name__}_"
                        ),
                        "grounded": False,
                        "model": "doc-intel-error",
                    }

            if wants_document_generation(prompt_text):
                try:
                    return generate_document_from_message(
                        client, prompt_text, db=db, user_id=user_id
                    )
                except Exception as exc:
                    return {
                        "reply": (
                            "I tried to create your document but something went wrong. "
                            "Please try again with the format (PDF, Word, Excel, or PowerPoint) and topic.\n\n"
                            f"_Detail: {type(exc).__name__}_"
                        ),
                        "grounded": False,
                        "model": "doc-gen-error",
                    }

            if wants_image_generation(prompt_text):
                try:
                    return generate_image_from_message(client, prompt_text)
                except Exception as exc:
                    return {
                        "reply": (
                            "I tried to create your image but the image service is busy right now. "
                            "Please try again in a moment, or describe your idea in more detail.\n\n"
                            f"_Detail: {type(exc).__name__}_"
                        ),
                        "grounded": False,
                        "model": "image-gen-error",
                    }

        if images:
            vision_msgs = _vision_messages(system, prompt_text, images, history)
            reply, model = _try_vision(client, vision_msgs)
        else:
            api_messages.append({"role": "user", "content": prompt_text})
            reply = _groq_completion(client, TEXT_MODEL, api_messages, max_tokens=1600)
            model = TEXT_MODEL

        if not reply:
            reply = _offline_answer(prompt_text, context)
            model = "offline-kb"

        return {
            "reply": reply,
            "grounded": bool(
                (context and "No specific local" not in context)
                or pdf_sections
                or images
            ),
            "model": model,
        }
    except Exception as exc:
        err_name = type(exc).__name__
        err_msg = str(exc)[:200]
        if images:
            return {
                "reply": (
                    "I received your image but couldn't analyse it right now. "
                    "Please try again in a moment, or describe what the image shows and I'll help from that.\n\n"
                    f"_Technical detail: {err_name}: {err_msg}_"
                ),
                "grounded": False,
                "model": "vision-error",
            }
        reply = _offline_answer(prompt_text, context)
        return {
            "reply": reply + f"\n\n_(Live model error: {err_name}: {err_msg})_",
            "grounded": True,
            "model": "offline-kb",
        }
