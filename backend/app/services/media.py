"""Extract text from PDFs and prepare images for vision models."""

from __future__ import annotations

import base64
import io
from typing import Any

from fastapi import HTTPException, UploadFile

MAX_PDF_BYTES = 12 * 1024 * 1024  # 12 MB
MAX_IMAGE_BYTES = 6 * 1024 * 1024  # 6 MB
MAX_FILES = 4
MAX_PDF_CHARS = 14000

ALLOWED_PDF = {"application/pdf", "application/x-pdf"}
ALLOWED_IMAGES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
}


def _guess_mime(filename: str, content_type: str | None) -> str:
    ct = (content_type or "").split(";")[0].strip().lower()
    if ct and ct != "application/octet-stream":
        return ct
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        return "application/pdf"
    if name.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if name.endswith(".png"):
        return "image/png"
    if name.endswith(".webp"):
        return "image/webp"
    if name.endswith(".gif"):
        return "image/gif"
    return ct or "application/octet-stream"


def extract_pdf_text(data: bytes, filename: str = "document.pdf") -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="PDF support not installed (pypdf)") from exc

    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read PDF ({filename})") from exc

    parts: list[str] = []
    for i, page in enumerate(reader.pages[:40], start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        text = text.strip()
        if text:
            parts.append(f"--- Page {i} ---\n{text}")

    joined = "\n\n".join(parts).strip()
    if not joined:
        raise HTTPException(
            status_code=400,
            detail=f"No extractable text in PDF '{filename}'. Try a text-based PDF (not a scanned image-only file).",
        )
    if len(joined) > MAX_PDF_CHARS:
        joined = joined[:MAX_PDF_CHARS] + "\n\n[… PDF truncated for length …]"
    return joined


async def process_uploads(files: list[UploadFile] | None) -> dict[str, Any]:
    """
    Returns:
      pdf_sections: list[{name, text}]
      images: list[{name, mime, data_url}]
      labels: short strings for UI/history
    """
    if not files:
        return {"pdf_sections": [], "images": [], "labels": []}

    usable = [f for f in files if f and f.filename]
    if len(usable) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Max {MAX_FILES} files per message")

    pdf_sections: list[dict[str, str]] = []
    images: list[dict[str, str]] = []
    labels: list[str] = []

    for upload in usable:
        raw = await upload.read()
        mime = _guess_mime(upload.filename or "", upload.content_type)
        name = upload.filename or "file"

        if mime in ALLOWED_PDF or name.lower().endswith(".pdf"):
            if len(raw) > MAX_PDF_BYTES:
                raise HTTPException(status_code=400, detail=f"PDF too large (max 12MB): {name}")
            text = extract_pdf_text(raw, name)
            pdf_sections.append({"name": name, "text": text})
            labels.append(f"PDF:{name}")
        elif mime in ALLOWED_IMAGES or name.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
            if len(raw) > MAX_IMAGE_BYTES:
                raise HTTPException(status_code=400, detail=f"Image too large (max 6MB): {name}")
            from app.services.image_vision import optimize_image_bytes, to_data_url

            optimized, out_mime = optimize_image_bytes(raw, mime)
            data_url = to_data_url(optimized, out_mime)
            images.append({"name": name, "mime": out_mime, "data_url": data_url})
            labels.append(f"Image:{name}")
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{name}'. Use PDF, JPG, PNG, WEBP, or GIF.",
            )

    return {"pdf_sections": pdf_sections, "images": images, "labels": labels}
