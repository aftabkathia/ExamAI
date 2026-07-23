"""Document Intelligence API — bulk PDF upload + business search."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from groq import Groq
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import CurrentUser
from app.config import get_settings
from app.database import get_db
from app.models import IntelDocument
from app.services.document_intelligence import (
    ask_documents,
    ingest_pdf,
    library_stats,
    list_documents,
)

router = APIRouter(prefix="/doc-intel", tags=["doc-intel"])

MAX_BATCH = 50
MAX_FILE_BYTES = 12 * 1024 * 1024


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class AskResponse(BaseModel):
    answer: str
    sources: list[dict[str, str]]
    documents_searched: int
    matches_found: int = 0


def _groq() -> Groq:
    cfg = get_settings()
    if not cfg.groq_api_key or cfg.groq_api_key.startswith("your_"):
        raise HTTPException(status_code=503, detail="GROQ_API_KEY required")
    return Groq(api_key=cfg.groq_api_key)


@router.get("/stats")
def stats(user: CurrentUser, db: Session = Depends(get_db)):
    return library_stats(db, user.id)


@router.get("/library")
def library(user: CurrentUser, db: Session = Depends(get_db)):
    return {
        "stats": library_stats(db, user.id),
        "documents": list_documents(db, user.id),
    }


@router.post("/upload")
async def upload_pdfs(
    user: CurrentUser,
    db: Session = Depends(get_db),
    files: list[UploadFile] = File(...),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    if len(files) > MAX_BATCH:
        raise HTTPException(status_code=400, detail=f"Max {MAX_BATCH} PDFs per batch")

    added: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []

    for upload in files:
        name = upload.filename or "document.pdf"
        if not name.lower().endswith(".pdf"):
            errors.append(f"{name}: not a PDF")
            continue
        raw = await upload.read()
        if len(raw) > MAX_FILE_BYTES:
            errors.append(f"{name}: too large (max 12MB)")
            continue
        if len(raw) < 100:
            errors.append(f"{name}: file empty")
            continue
        try:
            doc = ingest_pdf(db, user.id, name, raw)
            if doc:
                added.append(name)
            else:
                skipped.append(name)
        except Exception as exc:
            errors.append(f"{name}: {exc}")

    return {
        "added": added,
        "skipped_duplicates": skipped,
        "errors": errors,
        "stats": library_stats(db, user.id),
    }


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest, user: CurrentUser, db: Session = Depends(get_db)):
    result = ask_documents(db, user.id, payload.question.strip(), _groq())
    return AskResponse(
        answer=result["answer"],
        sources=result.get("sources", []),
        documents_searched=result.get("documents_searched", 0),
        matches_found=result.get("matches_found", 0),
    )


@router.delete("/library/{doc_id}")
def delete_document(doc_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    doc = (
        db.query(IntelDocument)
        .filter(IntelDocument.id == doc_id, IntelDocument.user_id == user.id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    return {"ok": True, "stats": library_stats(db, user.id)}
