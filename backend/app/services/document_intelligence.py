"""Document Intelligence — bulk PDF library + semantic search."""

from __future__ import annotations

import hashlib
import io
import re
from typing import Any

from groq import Groq
from sqlalchemy.orm import Session, joinedload

from app.models import IntelChunk, IntelDocument

TEXT_MODEL = "llama-3.3-70b-versatile"
MAX_DOCS_PER_USER = 500
MAX_PAGES = 150
CHUNK_SIZE = 1400
CHUNK_OVERLAP = 120

_SEARCH_PATTERNS = [
    re.compile(p, re.I)
    for p in (
        r"\bfind\s+(all|every|any)\b",
        r"\bwhich\s+(contracts?|invoices?|documents?|pdfs?|files?)\b",
        r"\b(search|look)\s+(my|through|in)\s+(documents?|pdfs?|files?|library)\b",
        r"\b(my|our)\s+(invoices?|contracts?|documents?|pdfs?)\b",
        r"\bdocuments?\s+(from|mention|about|regarding)\b",
        r"\bmention(s)?\s+(late\s+payment|payment|clause)\b",
        r"\blist\s+(all\s+)?(invoices?|contracts?)\b",
        r"\bdoc(?:ument)?\s+intel",
    )
]


def wants_doc_intel_query(message: str) -> bool:
    text = (message or "").strip()
    if len(text) < 8:
        return False
    return any(p.search(text) for p in _SEARCH_PATTERNS)


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9\u0600-\u06FF]{2,}", (text or "").lower())
    stop = {
        "the", "and", "for", "what", "who", "when", "where", "which", "how", "all",
        "from", "with", "that", "this", "have", "has", "was", "were", "are", "is",
        "can", "you", "please", "find", "my", "our", "any", "every",
    }
    return {w for w in words if w not in stop}


def _guess_kind(filename: str, text: str) -> str:
    blob = f"{filename} {text[:2000]}".lower()
    if "invoice" in blob:
        return "invoice"
    if "contract" in blob or "agreement" in blob:
        return "contract"
    if "receipt" in blob:
        return "receipt"
    return "document"


def extract_pdf_pages(data: bytes, filename: str) -> tuple[str, int]:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    parts: list[str] = []
    pages = min(len(reader.pages), MAX_PAGES)
    for i in range(pages):
        try:
            text = (reader.pages[i].extract_text() or "").strip()
        except Exception:
            text = ""
        if text:
            parts.append(f"--- Page {i + 1} ---\n{text}")
    joined = "\n\n".join(parts).strip()
    if not joined:
        raise ValueError(f"No extractable text in '{filename}'")
    return joined, pages


def _chunk_text(text: str) -> list[tuple[str, str]]:
    """Return list of (page_hint, chunk_text)."""
    sections = re.split(r"(--- Page \d+ ---)", text)
    chunks: list[tuple[str, str]] = []
    current_page = ""
    buf = ""
    for part in sections:
        if part.startswith("--- Page"):
            if buf.strip():
                chunks.extend(_split_buf(current_page, buf.strip()))
            current_page = part.replace("---", "").strip()
            buf = ""
        else:
            buf += part
    if buf.strip():
        chunks.extend(_split_buf(current_page, buf.strip()))
    if not chunks and text.strip():
        chunks.extend(_split_buf("", text.strip()))
    return chunks


def _split_buf(page_hint: str, text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        piece = text[start:end]
        if piece.strip():
            out.append((page_hint, piece.strip()))
        if end >= len(text):
            break
        start = end - CHUNK_OVERLAP
    return out


def ingest_pdf(
    db: Session,
    user_id: int,
    filename: str,
    raw: bytes,
) -> IntelDocument | None:
    file_hash = hashlib.sha256(raw).hexdigest()
    existing = (
        db.query(IntelDocument)
        .filter(IntelDocument.user_id == user_id, IntelDocument.file_hash == file_hash)
        .first()
    )
    if existing:
        return None

    count = db.query(IntelDocument).filter(IntelDocument.user_id == user_id).count()
    if count >= MAX_DOCS_PER_USER:
        raise ValueError(f"Library full (max {MAX_DOCS_PER_USER} PDFs)")

    full_text, page_count = extract_pdf_pages(raw, filename)
    kind = _guess_kind(filename, full_text)
    title = filename.rsplit(".", 1)[0] if "." in filename else filename

    doc = IntelDocument(
        user_id=user_id,
        filename=filename[:512],
        title=title[:512],
        doc_kind=kind,
        page_count=page_count,
        char_count=len(full_text),
        file_hash=file_hash,
    )
    db.add(doc)
    db.flush()

    for idx, (page_hint, chunk_text) in enumerate(_chunk_text(full_text)):
        db.add(
            IntelChunk(
                document_id=doc.id,
                chunk_index=idx,
                page_hint=page_hint[:50],
                text=chunk_text[:8000],
            )
        )
    db.commit()
    db.refresh(doc)
    return doc


def library_stats(db: Session, user_id: int) -> dict[str, Any]:
    docs = db.query(IntelDocument).filter(IntelDocument.user_id == user_id).all()
    kinds: dict[str, int] = {}
    for d in docs:
        kinds[d.doc_kind] = kinds.get(d.doc_kind, 0) + 1
    return {
        "total_documents": len(docs),
        "total_chunks": db.query(IntelChunk)
        .join(IntelDocument)
        .filter(IntelDocument.user_id == user_id)
        .count(),
        "by_kind": kinds,
    }


def list_documents(db: Session, user_id: int, limit: int = 200) -> list[dict[str, Any]]:
    rows = (
        db.query(IntelDocument)
        .filter(IntelDocument.user_id == user_id)
        .order_by(IntelDocument.uploaded_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "title": r.title,
            "doc_kind": r.doc_kind,
            "page_count": r.page_count,
            "char_count": r.char_count,
            "uploaded_at": r.uploaded_at.isoformat() if r.uploaded_at else None,
        }
        for r in rows
    ]


def search_chunks(db: Session, user_id: int, query: str, limit: int = 25) -> list[dict[str, Any]]:
    qtokens = _tokens(query)
    if not qtokens:
        qtokens = set(query.lower().split())

    rows = (
        db.query(IntelChunk)
        .options(joinedload(IntelChunk.document))
        .join(IntelDocument)
        .filter(IntelDocument.user_id == user_id)
        .all()
    )
    scored: list[tuple[int, IntelChunk]] = []
    for chunk in rows:
        doc = chunk.document
        blob = f"{doc.filename} {doc.title} {doc.doc_kind} {chunk.text} {chunk.page_hint}".lower()
        score = sum(3 if t in doc.filename.lower() else 1 for t in qtokens if t in blob)
        # Boost month names for "April" style queries
        for t in qtokens:
            if t in ("january", "february", "march", "april", "may", "june",
                     "july", "august", "september", "october", "november", "december",
                     "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec"):
                if t[:3] in blob or t in blob:
                    score += 4
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    results: list[dict[str, Any]] = []
    seen: set[int] = set()
    for score, chunk in scored:
        if chunk.document_id in seen and len(results) > limit:
            continue
        seen.add(chunk.document_id)
        doc = chunk.document
        results.append(
            {
                "document_id": doc.id,
                "filename": doc.filename,
                "doc_kind": doc.doc_kind,
                "page_hint": chunk.page_hint,
                "snippet": chunk.text[:500],
                "score": score,
            }
        )
        if len(results) >= limit:
            break
    return results


def ask_documents(
    db: Session,
    user_id: int,
    question: str,
    client: Groq,
) -> dict[str, Any]:
    total = db.query(IntelDocument).filter(IntelDocument.user_id == user_id).count()
    if total == 0:
        return {
            "answer": (
                "Your document library is empty. Upload PDFs in the **Doc Intel** tab "
                "(invoices, contracts, reports), then ask questions here."
            ),
            "sources": [],
            "documents_searched": 0,
        }

    hits = search_chunks(db, user_id, question, limit=20)
    if not hits:
        hits = search_chunks(db, user_id, " ".join(list(_tokens(question))[:8]), limit=15)

    context_parts = []
    sources: list[dict[str, str]] = []
    for h in hits[:18]:
        context_parts.append(
            f"### {h['filename']} ({h['doc_kind']}) {h['page_hint']}\n{h['snippet']}"
        )
        sources.append(
            {
                "filename": h["filename"],
                "doc_kind": h["doc_kind"],
                "page": h["page_hint"],
            }
        )

    context = "\n\n".join(context_parts) if context_parts else "No close keyword matches."

    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a document intelligence assistant for businesses. "
                    "Answer ONLY from the provided PDF excerpts. "
                    "List matching documents clearly with filename. "
                    "If asked to find invoices/contracts, filter by content. "
                    "If insufficient data, say what was searched and what's missing. "
                    "Cite sources like: **invoice_april.pdf** (Page 2)."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"DOCUMENT LIBRARY: {total} PDFs indexed.\n\n"
                    f"RETRIEVED EXCERPTS:\n{context[:14000]}\n\n"
                    f"QUESTION: {question}"
                ),
            },
        ],
        temperature=0.15,
        max_tokens=1800,
    )
    answer = (response.choices[0].message.content or "").strip()
    return {
        "answer": answer,
        "sources": sources[:10],
        "documents_searched": total,
        "matches_found": len(hits),
    }


def build_intel_context_summary(db: Session, user_id: int) -> str:
    stats = library_stats(db, user_id)
    if stats["total_documents"] == 0:
        return ""
    kinds = ", ".join(f"{k}: {v}" for k, v in stats["by_kind"].items())
    return (
        f"\n\n## DOCUMENT INTELLIGENCE LIBRARY\n"
        f"User has **{stats['total_documents']}** PDFs indexed ({kinds}). "
        f"They can search with questions like 'find invoices from April'. "
        f"Route document-search questions to their library."
    )
