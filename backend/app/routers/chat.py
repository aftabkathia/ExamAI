import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from groq import Groq
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth import CurrentUser
from app.config import get_settings
from app.database import get_db
from app.services.media import process_uploads
from app.services.tutor import chat_completion
from app.services.user_memory import get_persisted_history, list_memories, persist_turn
from app.services.voice import (
    detect_language,
    process_audio_upload,
    text_to_speech,
    transcribe_audio,
)

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)
    voice_reply: bool = False


class ChatResponse(BaseModel):
    reply: str
    grounded: bool = False
    model: str = "examai-tutor"
    attachments: list[str] = []
    generated_images: list[str] = []
    generated_files: list[dict[str, str]] = []
    memory_count: int = 0
    sources: list[dict[str, str]] = []
    reply_language: str = "en"
    audio_base64: str | None = None
    audio_mime: str | None = None


def _groq_client() -> Groq | None:
    cfg = get_settings()
    if cfg.groq_api_key and not cfg.groq_api_key.startswith("your_"):
        return Groq(api_key=cfg.groq_api_key)
    return None


def _persist_turn(db: Session, user_id: int, user_message: str, reply: str) -> None:
    if not user_message.strip() or not reply.strip():
        return
    persist_turn(db, user_id, user_message.strip(), reply.strip(), _groq_client())


def _chat_response(result: dict, voice: dict, memory_count: int = 0) -> ChatResponse:
    return ChatResponse(
        reply=result["reply"],
        grounded=result.get("grounded", False),
        model=result.get("model", "examai-tutor"),
        attachments=result.get("attachments", []),
        generated_images=[
            img["data_url"] for img in result.get("generated_images", [])
        ],
        generated_files=result.get("generated_files", []),
        memory_count=memory_count,
        sources=result.get("sources", []),
        reply_language=voice["reply_language"],
        audio_base64=voice["audio_base64"],
        audio_mime=voice["audio_mime"],
    )


class TranscribeResponse(BaseModel):
    text: str
    language: str


class SpeakRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    language: str | None = None


class SpeakResponse(BaseModel):
    audio_base64: str
    mime: str
    voice: str
    language: str


async def _maybe_voice(reply: str, voice_reply: bool, user_message: str) -> dict:
    lang = detect_language(user_message or reply)
    out: dict = {"reply_language": lang, "audio_base64": None, "audio_mime": None}
    if voice_reply and reply.strip():
        try:
            tts = await text_to_speech(reply, lang)
            out["audio_base64"] = tts["audio_base64"]
            out["audio_mime"] = tts["mime"]
            out["reply_language"] = tts["language"]
        except HTTPException:
            pass
    return out


@router.post("/", response_model=ChatResponse)
async def chat(payload: ChatRequest, user: CurrentUser, db: Session = Depends(get_db)):
    history = [{"role": m.role, "content": m.content} for m in payload.history]
    result = chat_completion(
        db, history, payload.message.strip(), user_id=user.id
    )
    voice = await _maybe_voice(result["reply"], payload.voice_reply, payload.message)
    _persist_turn(db, user.id, payload.message.strip(), result["reply"])
    mem_count = len(list_memories(db, user.id))
    return _chat_response(result, voice, mem_count)


@router.post("/upload", response_model=ChatResponse)
async def chat_with_files(
    user: CurrentUser,
    db: Session = Depends(get_db),
    message: str = Form(default=""),
    history: str = Form(default="[]"),
    voice_reply: bool = Form(default=False),
    files: list[UploadFile] = File(default=[]),
):
    try:
        history_raw = json.loads(history or "[]")
        if not isinstance(history_raw, list):
            raise ValueError("history must be a list")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid history JSON") from exc

    hist: list[dict[str, str]] = []
    for item in history_raw[-20:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
            hist.append({"role": role, "content": content.strip()[:8000]})

    media = await process_uploads(files)
    if not message.strip() and not media["pdf_sections"] and not media["images"]:
        raise HTTPException(status_code=400, detail="Send a message or attach a PDF/image")

    result = chat_completion(
        db,
        hist,
        message.strip(),
        pdf_sections=media["pdf_sections"],
        images=media["images"],
        user_id=user.id,
    )
    voice = await _maybe_voice(result["reply"], voice_reply, message)
    user_text = message.strip() or f"Uploaded: {', '.join(media['labels'])}"
    _persist_turn(db, user.id, user_text, result["reply"])
    mem_count = len(list_memories(db, user.id))
    out = _chat_response(result, voice, mem_count)
    out.attachments = media["labels"]
    return out


@router.get("/history")
def chat_history(user: CurrentUser, db: Session = Depends(get_db)):
    """Load persisted chat for this user (personal memory)."""
    messages = get_persisted_history(db, user.id, limit=40)
    memories = list_memories(db, user.id)
    return {"messages": messages, "memory_count": len(memories)}


@router.get("/memory")
def chat_memory(user: CurrentUser, db: Session = Depends(get_db)):
    """List what the assistant remembers about this user."""
    return {"memories": list_memories(db, user.id)}


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(user: CurrentUser, audio: UploadFile = File(...)):
    """Speech-to-text via Groq Whisper — supports Urdu, Roman Urdu, English, and more."""
    raw = await process_audio_upload(audio)
    result = await transcribe_audio(raw, audio.filename or "voice.webm")
    return TranscribeResponse(text=result["text"], language=result["language"])


@router.post("/speak", response_model=SpeakResponse)
async def speak(payload: SpeakRequest, user: CurrentUser):
    """Text-to-speech — Urdu or English voice."""
    lang = payload.language or detect_language(payload.text)
    tts = await text_to_speech(payload.text, lang)
    return SpeakResponse(
        audio_base64=tts["audio_base64"],
        mime=tts["mime"],
        voice=tts["voice"],
        language=tts["language"],
    )


@router.get("/suggestions")
def suggestions(user: CurrentUser):
    return {
        "suggestions": [
            "Pakistan Resolution kab pass hui?",
            "When was the Pakistan Resolution passed?",
            "Explain photosynthesis in simple Roman Urdu",
            "Latest AI trends explain karo",
            "If 15% of a number is 45, what is 40%?",
            "Outline essay on Ideology of Pakistan",
            "1857 War of Independence ke causes",
            "Summarise this PDF for exam prep",
            "Draw a diagram of the water cycle",
            "Create PDF notes on Pakistan Resolution",
            "Make Excel sheet of CSS everyday science MCQs",
            "Find all invoices from April",
            "Which contracts mention late payment?",
            "Health tips for students",
            "Python list vs tuple difference",
        ]
    }
