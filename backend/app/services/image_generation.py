"""AI image generation — Groq prompt expansion + Pollinations rendering."""

from __future__ import annotations

import base64
import re
import urllib.parse
from typing import Any

import httpx
from groq import Groq

TEXT_MODEL = "llama-3.3-70b-versatile"

_GEN_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\b(draw|create|generate|make|design|paint|sketch|illustrate|render|produce)\b.{0,40}\b("
        r"image|picture|photo|illustration|diagram|logo|poster|art|drawing|graphic|visual|icon|banner)\b",
        r"\b(image|picture|photo|tasveer|drawing|diagram)\b.{0,30}\b("
        r"banao|banado|bana\s*do|banani|create|generate|draw|design|make)\b",
        r"\b(tasveer|image|picture)\s*(banao|banado|bana\s*do|banani)\b",
        r"\bshow\s+me\s+(a|an)\s+(picture|image|photo|drawing|diagram)\b",
        r"\bdraw\s+me\b",
        r"\bmake\s+me\s+(an?\s+)?(image|picture|illustration|diagram)\b",
        r"\bcreate\s+(a\s+)?visual\b",
        r"\bdiagram\s+of\b",
        r"\billustrat(e|ion)\s+of\b",
    )
]

_ANALYSIS_ONLY = re.compile(
    r"\b(explain|describe|analyse|analyze|what\s+is\s+in|read\s+this|solve\s+this|"
    r"summarize|summarise|transcribe|ocr)\b",
    re.IGNORECASE,
)

PROMPT_SYSTEM = """You write prompts for an AI image generator.
Given the user's request, output ONE detailed English prompt (80–120 words) describing:
subject, scene, style, lighting, colors, composition, and any text labels if needed.
For educational diagrams: clear labels, white or light background, textbook style.
Output ONLY the prompt — no quotes, no explanation."""


def wants_image_generation(message: str, has_uploads: bool = False) -> bool:
    """True when the user wants a new image created (not analysing an upload)."""
    if has_uploads:
        return False
    text = (message or "").strip()
    if len(text) < 4:
        return False
    if not any(p.search(text) for p in _GEN_PATTERNS):
        return False
    # "explain this image" should not trigger generation when analysing
    if _ANALYSIS_ONLY.search(text) and not re.search(
        r"\b(draw|create|generate|make|design|banao|bana)\b", text, re.IGNORECASE
    ):
        return False
    return True


def _expand_prompt(client: Groq, user_message: str) -> str:
    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[
            {"role": "system", "content": PROMPT_SYSTEM},
            {"role": "user", "content": user_message},
        ],
        temperature=0.4,
        max_tokens=300,
    )
    prompt = (response.choices[0].message.content or "").strip()
    prompt = re.sub(r"^[\"']|[\"']$", "", prompt)
    return prompt[:900] if prompt else user_message[:400]


def _fetch_image(prompt: str, width: int = 1024, height: int = 1024) -> bytes:
    encoded = urllib.parse.quote(prompt, safe="")
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={width}&height={height}&nologo=true&enhance=true"
    )
    with httpx.Client(timeout=120.0, follow_redirects=True) as http:
        resp = http.get(url, headers={"User-Agent": "ExamAI/1.0"})
        resp.raise_for_status()
        data = resp.content
        if len(data) < 500:
            raise ValueError("Image provider returned empty data")
        return data


def generate_image_from_message(client: Groq, user_message: str) -> dict[str, Any]:
    """Expand prompt with Groq, render image, return reply + data URL."""
    diffusion_prompt = _expand_prompt(client, user_message)
    raw = _fetch_image(diffusion_prompt)
    b64 = base64.b64encode(raw).decode("ascii")
    mime = "image/jpeg" if raw[:3] == b"\xff\xd8\xff" else "image/png"
    data_url = f"data:{mime};base64,{b64}"

    short = user_message.strip()
    if len(short) > 80:
        short = short[:77] + "…"

    reply = (
        f"**Image created** for: _{short}_\n\n"
        "The image is shown below. Ask me to change style, colors, labels, or create another version."
    )
    return {
        "reply": reply,
        "generated_images": [{"name": "generated.png", "mime": mime, "data_url": data_url}],
        "grounded": False,
        "model": "image-gen",
        "prompt_used": diffusion_prompt,
    }
