import json
import logging
import re

from openai import OpenAI

from ..ports import KnowledgeNoteProvider, NoteResult

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a knowledge extraction assistant. "
    "Given a transcript, you identify actionable knowledge artifacts. "
    "Respond ONLY with a valid JSON array and no other text."
)

_MAX_NOTE_WORDS = 48
_GENERIC_REFLECTION_PREFIXES = (
    "welche aussage aus dem inhalt",
    "welcher aussage aus dem inhalt",
    "was waere die wichtigste erkenntnis",
)
_GENERIC_ACTION_PHRASES = ("zum beispiel:",)

_USER_PROMPT_TEMPLATE = """Analyze the following transcript and generate 4-6 knowledge notes.

For each note, produce a JSON object with these exact keys:
- "kind": one of "insight", "action", "reflection", "question"
- "title": short descriptive title (max 80 chars)
- "content_markdown": the note body in Markdown (max 2 short sentences or 2 bullets)

Rules:
- "insight": a key claim, mental model or lesson from the content; keep it concise
- "action": a concrete next step the listener could do in under 30 minutes; start with a verb
- "reflection": an open question that exposes a tension, tradeoff or blind spot from the content
- "question": a clarifying question about the material itself
- Do NOT copy the transcript verbatim. Synthesize and distill aggressively.
- Do NOT include long quoted transcript passages.
- Keep every note under 45 words.
- Skip weak or generic notes instead of padding the result.
- Write in the same language as the transcript.

Return ONLY the JSON array, no preamble, no explanation.

Transcript:
{transcript}
"""


def _word_count(text: str) -> int:
    return len(text.split())


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split()).strip()


def _looks_like_generic_reflection(text: str) -> bool:
    normalized = _normalize_whitespace(text).lower()
    return normalized.startswith(_GENERIC_REFLECTION_PREFIXES)


def _looks_like_generic_action(text: str) -> bool:
    normalized = _normalize_whitespace(text).lower()
    return any(phrase in normalized for phrase in _GENERIC_ACTION_PHRASES)


def _filter_note_results(results: list[NoteResult]) -> list[NoteResult]:
    filtered: list[NoteResult] = []
    for result in results:
        content = _normalize_whitespace(result.content_markdown)
        if not content:
            continue
        if _word_count(content) > _MAX_NOTE_WORDS:
            continue
        if result.kind == "reflection" and _looks_like_generic_reflection(content):
            continue
        if result.kind == "action" and _looks_like_generic_action(content):
            continue
        filtered.append(
            NoteResult(
                title=result.title.strip()[:255],
                content_markdown=content,
                kind=result.kind,
            )
        )
    return filtered


def _extract_sentences(transcript_text: str) -> list[str]:
    condensed_text = _normalize_whitespace(transcript_text)
    parts = re.split(r"(?<=[.!?])\s+", condensed_text)
    return [part.strip(" .") for part in parts if part.strip()]


class OpenAICompatibleNoteProvider:
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def generate(self, transcript_text: str, language_code: str = "") -> list[NoteResult]:
        prompt = _USER_PROMPT_TEMPLATE.format(transcript=transcript_text[:12000])
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=2048,
            temperature=0.4,
        )
        raw = (response.choices[0].message.content or "").strip()

        try:
            items = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Note provider returned non-JSON response; attempting extraction")
            start = raw.find("[")
            end = raw.rfind("]") + 1
            if start == -1 or end == 0:
                logger.error("Could not extract JSON array from note provider response")
                return []
            items = json.loads(raw[start:end])

        results = []
        for item in items:
            if not isinstance(item, dict):
                continue
            kind = item.get("kind", "general")
            title = str(item.get("title", "Untitled"))[:255]
            content = str(item.get("content_markdown", ""))
            results.append(NoteResult(title=title, content_markdown=content, kind=kind))

        return _filter_note_results(results)


class StubNoteProvider:
    """Returns deterministic stub notes for local development without an AI backend."""

    def generate(self, transcript_text: str, language_code: str = "") -> list[NoteResult]:
        sentences = _extract_sentences(transcript_text)
        first = (
            sentences[0]
            if sentences
            else "Der Inhalt enthaelt mehrere anschlussfaehige Gedanken."
        )
        second = (
            sentences[1]
            if len(sentences) > 1
            else "Ein naechster Schritt koennte sein, die zentrale Aussage bewusst zu notieren."
        )
        third = (
            sentences[2]
            if len(sentences) > 2
            else "Mehr Spielraum entsteht oft dort, wo feste Annahmen geprueft werden."
        )

        results = [
            NoteResult(
                kind="insight",
                title="Schlüsselerkenntnis aus dem Inhalt",
                content_markdown=(
                    f"Zentrale Erkenntnis: {first}. "
                    "Der Inhalt macht deutlich, dass daraus ein konkreter Blick "
                    "auf eigenes Verhalten folgen sollte."
                ),
            ),
            NoteResult(
                kind="action",
                title="Konkrete Handlungsempfehlung",
                content_markdown=(
                    "Notiere heute eine Ueberzeugung oder Gewohnheit aus dem "
                    "Inhalt, die du bei dir wiedererkennst. "
                    f"Pruefe anschliessend mit '{second[:80]}' einen kleinen "
                    "Gegenentwurf fuer die naechste konkrete Situation."
                ),
            ),
            NoteResult(
                kind="reflection",
                title="Reflexionsfrage",
                content_markdown=(
                    f"Wo erzeugt die Haltung '{third[:90]}' in deinem Alltag eher "
                    "Sicherheit als Klarheit? "
                    "Was wuerde sich veraendern, wenn du diese Annahme probeweise lockerst?"
                ),
            ),
        ]
        return _filter_note_results(results)


def get_note_provider() -> KnowledgeNoteProvider:
    from django.conf import settings

    provider = getattr(settings, "KNOWLEDGE_NOTE_PROVIDER", "stub")

    if provider == "openai_compatible":
        return OpenAICompatibleNoteProvider(
            base_url=settings.AI_HUB_BASE_URL,
            api_key=settings.AI_HUB_API_KEY,
            model=settings.AI_HUB_MODEL,
        )

    return StubNoteProvider()
