"""Speech-to-text (Groq Whisper) and text-to-speech (edge-tts)."""

from __future__ import annotations

import base64
import io
import re
import tempfile
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile
from groq import Groq

from app.config import get_settings

MAX_AUDIO_BYTES = 8 * 1024 * 1024  # 8 MB
ALLOWED_AUDIO = {
    "audio/webm",
    "audio/ogg",
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/m4a",
    "video/webm",  # some browsers send webm as video
}

WHISPER_MODEL = "whisper-large-v3"

VOICES = {
    "en": "en-US-JennyNeural",
    "ur": "ur-PK-UzmaNeural",
    "ur-male": "ur-PK-AsadNeural",
    "hi": "hi-IN-SwaraNeural",
    "ar": "ar-SA-ZariyahNeural",
}

# Roman Urdu / Hinglish hints
_ROMAN_URDU = re.compile(
    r"\b(kya|kia|hai|hain|ho|ka|ki|ke|ko|se|mein|main|mera|meri|ap|aap|tum|"
    r"ye|wo|kahan|kab|kyun|kyon|kaise|kesy|batao|bata|salam|shukriya|"
    r"theek|acha|accha|nahi|nahin|haan|han|bhai|yar|jan|karo|karna|"
    r"mujhe|tumhe|hum|aapka|konsa|kon|kis|kisi|par|pe|aur|lekin|magar)\b",
    re.I,
)


def detect_language(text: str) -> str:
    """Return voice key: en | ur | hi | ar."""
    if not text.strip():
        return "en"
    # Urdu/Arabic script
    if re.search(r"[\u0600-\u06FF\u0750-\u077F]", text):
        return "ur"
    if re.search(r"[\u0900-\u097F]", text):
        return "hi"
    if _ROMAN_URDU.search(text):
        return "ur"
    return "en"


async def transcribe_audio(data: bytes, filename: str = "audio.webm") -> dict[str, Any]:
    settings = get_settings()
    if not settings.groq_api_key or settings.groq_api_key.startswith("your_"):
        raise HTTPException(status_code=503, detail="Groq API key required for voice input")

    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=400, detail="Audio too large (max 8MB)")

    suffix = Path(filename).suffix or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        client = Groq(api_key=settings.groq_api_key)
        with open(tmp_path, "rb") as f:
            result = client.audio.transcriptions.create(
                file=f,
                model=WHISPER_MODEL,
                language=None,  # auto-detect
                response_format="verbose_json",
                temperature=0,
            )
        text = (getattr(result, "text", None) or "").strip()
        lang = getattr(result, "language", None) or detect_language(text)
        if not text:
            raise HTTPException(status_code=400, detail="Could not understand audio. Speak clearly and try again.")
        return {"text": text, "language": lang}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {type(exc).__name__}") from exc
    finally:
        Path(tmp_path).unlink(missing_ok=True)


async def text_to_speech(text: str, lang: str | None = None) -> dict[str, str]:
    """Generate MP3 audio from text. Returns base64 + mime + voice used."""
    try:
        import edge_tts
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="TTS not installed (edge-tts)") from exc

    clean = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    clean = re.sub(r"`([^`]+)`", r"\1", clean)
    clean = re.sub(r"[_#>*\[\]()]", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    if not clean:
        raise HTTPException(status_code=400, detail="Nothing to speak")
    # TTS length cap
    if len(clean) > 3500:
        clean = clean[:3500] + "..."

    voice_key = lang if lang in VOICES else detect_language(text)
    voice = VOICES.get(voice_key, VOICES["en"])

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        out_path = tmp.name

    try:
        communicate = edge_tts.Communicate(clean, voice)
        await communicate.save(out_path)
        audio_bytes = Path(out_path).read_bytes()
        b64 = base64.b64encode(audio_bytes).decode("ascii")
        return {
            "audio_base64": b64,
            "mime": "audio/mpeg",
            "voice": voice,
            "language": voice_key,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"TTS failed: {type(exc).__name__}") from exc
    finally:
        Path(out_path).unlink(missing_ok=True)


async def process_audio_upload(upload: UploadFile) -> bytes:
    raw = await upload.read()
    ct = (upload.content_type or "").split(";")[0].strip().lower()
    name = (upload.filename or "").lower()
    ok = ct in ALLOWED_AUDIO or name.endswith((".webm", ".ogg", ".mp3", ".wav", ".m4a"))
    if not ok:
        raise HTTPException(status_code=400, detail="Unsupported audio. Use webm, ogg, mp3, or wav.")
    return raw
