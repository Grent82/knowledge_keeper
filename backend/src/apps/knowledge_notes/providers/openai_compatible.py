import json
import logging

from openai import OpenAI

from ..ports import KnowledgeNoteProvider, NoteResult

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a knowledge extraction assistant. "
    "Given a transcript, you identify actionable knowledge artifacts. "
    "Respond ONLY with a valid JSON array and no other text."
)

_USER_PROMPT_TEMPLATE = """Analyze the following transcript and generate 4-6 knowledge notes.

For each note, produce a JSON object with these exact keys:
- "kind": one of "insight", "action", "reflection", "question"
- "title": short descriptive title (max 80 chars)
- "content_markdown": the note body in Markdown (2-4 sentences or bullet points)

Rules:
- "insight": a key claim, mental model or lesson from the content
- "action": a concrete step the listener could take
- "reflection": an open question the content raises worth thinking about
- "question": a clarifying question about the material itself
- Do NOT copy the transcript verbatim. Synthesize and distill.
- Write in the same language as the transcript.

Return ONLY the JSON array, no preamble, no explanation.

Transcript:
{transcript}
"""


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

        return results


class StubNoteProvider:
    """Returns deterministic stub notes for local development without an AI backend."""

    def generate(self, transcript_text: str, language_code: str = "") -> list[NoteResult]:
        return [
            NoteResult(
                kind="insight",
                title="Schlüsselerkenntnis aus dem Inhalt",
                content_markdown="Dies ist eine automatisch generierte Platzhalter-Notiz. "
                "Sie wird durch echte KI-Inhalte ersetzt, sobald ein Provider konfiguriert ist.",
            ),
            NoteResult(
                kind="action",
                title="Konkrete Handlungsempfehlung",
                content_markdown="Konfiguriere `KNOWLEDGE_NOTE_PROVIDER=openai_compatible` "
                "in den Django-Settings, um echte Notizen zu erzeugen.",
            ),
            NoteResult(
                kind="reflection",
                title="Reflexionsfrage",
                content_markdown="Was wäre die wichtigste Erkenntnis aus diesem Inhalt für dich?",
            ),
        ]


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
