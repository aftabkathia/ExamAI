"""Prepare images for vision models — resize, normalize format, base64."""

from __future__ import annotations

import base64
import io

from fastapi import HTTPException

MAX_IMAGE_BYTES = 6 * 1024 * 1024
MAX_VISION_DIM = 2048
JPEG_QUALITY = 88


def optimize_image_bytes(raw: bytes, mime: str) -> tuple[bytes, str]:
    """Resize/compress image for reliable vision API calls. Returns (bytes, mime)."""
    try:
        from PIL import Image
    except ImportError:
        return raw, mime if mime.startswith("image/") else "image/jpeg"

    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid or corrupted image file") from exc

    if img.mode in ("RGBA", "P", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    w, h = img.size
    if max(w, h) > MAX_VISION_DIM:
        img.thumbnail((MAX_VISION_DIM, MAX_VISION_DIM), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    out = buf.getvalue()
    if len(out) > MAX_IMAGE_BYTES:
        # second pass — lower quality
        buf2 = io.BytesIO()
        img.save(buf2, format="JPEG", quality=72, optimize=True)
        out = buf2.getvalue()
    return out, "image/jpeg"


def to_data_url(raw: bytes, mime: str) -> str:
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"
