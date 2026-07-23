import json
import re
from typing import Any

from groq import Groq

from app.config import get_settings
from app.services.question_bank import pick_question, normalize_topic

settings = get_settings()

TOPIC_RULES = {
    "everyday science": "ONLY natural science of daily life: biology, chemistry, physics of environment, human body, space basics. NEVER politics, history, geography capitals, or current affairs.",
    "general knowledge": "World GK, organizations, geography, sports, currencies, famous facts. NOT deep science formulas.",
    "mathematics": "ONLY arithmetic, algebra, geometry, percentages, ratios, probability, sequences.",
    "computer science": "ONLY computing: hardware, software, networks, databases, programming concepts, binary.",
    "english": "ONLY grammar, vocabulary, idioms, synonyms/antonyms, sentence correction.",
    "biology": "ONLY living systems: cells, physiology, genetics, ecology — MDCAT style.",
    "chemistry": "ONLY chemical concepts, reactions, periodic table, acids/bases — exam style.",
    "physics": "ONLY mechanics, electricity, waves, optics, modern physics basics.",
    "pakistan studies": "ONLY Pakistan history, geography, constitution, movement, leaders.",
    "islamic studies": "ONLY Quran, Hadith, Seerah, pillars, Islamic history basics.",
    "current affairs": "International orgs, major geopolitical frameworks, Pakistan foreign-policy structures. Avoid unverifiable yesterday headlines.",
    "analytical reasoning": "ONLY IQ: series, analogies, odd-one-out, syllogisms, seating/blood relations.",
    "history": "World and subcontinent history — empires, wars, revolutions, dates.",
    "urdu": "Urdu literature, grammar, poets, and literary terms.",
}

SYSTEM_PROMPT = """You are a senior examiner for Pakistani competitive exams (CSS, MDCAT, ECAT, NET, NTS, PPSC, FPSC, OTS).
Write ORIGINAL, exam-standard MCQs that a serious candidate would face.

Return ONLY valid JSON (no markdown):
{
  "text": "question stem",
  "option_a": "...",
  "option_b": "...",
  "option_c": "...",
  "option_d": "...",
  "correct_option": "A|B|C|D",
  "explanation": "2–4 sentence explanation with the reasoning",
  "difficulty": "easy|medium|hard"
}

Hard rules:
1. The question MUST be 100% about the given TOPIC — never drift to another subject.
2. Exactly one correct option; distractors must be plausible.
3. Competitive difficulty — not trivia for children.
4. Prefer Pakistan-exam framing when the topic allows.
5. Do NOT repeat any question listed in the exclusion list.
"""


def _extract_json(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if fence:
        raw = fence.group(1).strip()
    return json.loads(raw)


def _validate_question(data: dict[str, Any]) -> dict[str, Any]:
    required = ["text", "option_a", "option_b", "option_c", "option_d", "correct_option", "explanation"]
    for key in required:
        if key not in data or not str(data[key]).strip():
            raise ValueError(f"Missing field: {key}")
    correct = str(data["correct_option"]).strip().upper()
    if correct not in {"A", "B", "C", "D"}:
        raise ValueError("Invalid correct_option")
    difficulty = str(data.get("difficulty", "medium")).lower()
    if difficulty not in {"easy", "medium", "hard"}:
        difficulty = "medium"
    return {
        "text": str(data["text"]).strip(),
        "option_a": str(data["option_a"]).strip(),
        "option_b": str(data["option_b"]).strip(),
        "option_c": str(data["option_c"]).strip(),
        "option_d": str(data["option_d"]).strip(),
        "correct_option": correct,
        "explanation": str(data["explanation"]).strip(),
        "difficulty": difficulty,
        "source": "llm",
    }


def generate_mcq(
    exam_name: str,
    topic_name: str,
    difficulty: str = "medium",
    weak_focus: bool = False,
    exclude_texts: set[str] | None = None,
) -> dict[str, Any]:
    """Generate a topic-faithful MCQ. Prefers bank; uses Groq when configured."""
    exclude_texts = exclude_texts or set()
    key = normalize_topic(topic_name)
    topic_rule = TOPIC_RULES.get(key, f"Stay strictly on: {topic_name}.")

    # Curated bank first (topic-accurate, competitive, no mislabeling)
    bank_q = pick_question(topic_name, difficulty=difficulty, exclude_texts=exclude_texts)

    use_llm = bool(settings.groq_api_key) and not settings.groq_api_key.startswith("your_")

    # Use LLM only when bank is exhausted for this topic (or to add variety if bank empty)
    if bank_q and (not use_llm or len(exclude_texts) < 8):
        return bank_q

    if use_llm:
        focus_note = " Student is weak — make it diagnostically useful." if weak_focus else ""
        exclude_preview = list(exclude_texts)[:12]
        user_prompt = (
            f"Exam: {exam_name}\n"
            f"Topic: {topic_name}\n"
            f"Topic lock: {topic_rule}\n"
            f"Difficulty: {difficulty}\n"
            f"Do NOT write questions similar to these:\n"
            + "\n".join(f"- {t}" for t in exclude_preview)
            + f"\nGenerate one ORIGINAL MCQ strictly on this topic only.{focus_note}"
        )
        try:
            client = Groq(api_key=settings.groq_api_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.9,
                max_tokens=900,
            )
            content = response.choices[0].message.content or ""
            q = _validate_question(_extract_json(content))
            if q["text"] not in exclude_texts:
                return q
        except Exception:
            pass

    if bank_q:
        return bank_q

    bank_q = pick_question(topic_name, difficulty="easy", exclude_texts=exclude_texts)
    if bank_q:
        return bank_q

    return {
        "text": f"Which statement is most relevant to studying {topic_name}?",
        "option_a": "An unrelated political trivia fact",
        "option_b": "A foundational principle within this topic",
        "option_c": "A random sports score",
        "option_d": "A currency exchange code",
        "correct_option": "B",
        "explanation": "Stay on-topic. Open Notes for this subject for structured revision.",
        "difficulty": difficulty,
        "source": "fallback",
    }
