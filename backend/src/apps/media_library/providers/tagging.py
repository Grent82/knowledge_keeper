import json
import logging

from openai import OpenAI

from ..ports import TaggingProvider

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a tagging assistant for a German-language knowledge library. "
    "Return ONLY a valid JSON array of strings and nothing else."
)

_USER_PROMPT_TEMPLATE = """Analyze the following text and suggest 3-5 concise German tags.

Rules:
- Tags must be in German
- Each tag is lowercase, 1-3 words max, no punctuation
- Tags should capture the main topics, concepts or persons
- Return ONLY a JSON array of strings, e.g. ["lernen", "gedächtnis", "methodik"]

Text:
{text}
"""


class OpenAICompatibleTaggingProvider:
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def suggest_tags(self, source_text: str) -> list[str]:
        prompt = _USER_PROMPT_TEMPLATE.format(text=source_text[:8000])
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=128,
            temperature=0.2,
        )
        raw = (response.choices[0].message.content or "").strip()

        try:
            tags = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Tagging provider returned non-JSON: %r", raw[:200])
            start, end = raw.find("["), raw.rfind("]") + 1
            if start == -1 or end == 0:
                return []
            tags = json.loads(raw[start:end])

        return [str(t).strip().lower() for t in tags if isinstance(t, str) and t.strip()]


class StubTaggingProvider:
    """Returns deterministic stub tags for local development."""

    def suggest_tags(self, source_text: str) -> list[str]:
        return ["wissensvermittlung", "lernen", "persönlichkeitsentwicklung"]


def get_tagging_provider() -> TaggingProvider:
    from django.conf import settings

    provider = getattr(settings, "TAGGING_PROVIDER", "stub")

    if provider == "openai_compatible":
        return OpenAICompatibleTaggingProvider(
            base_url=settings.AI_HUB_BASE_URL,
            api_key=settings.AI_HUB_API_KEY,
            model=settings.AI_HUB_MODEL,
        )

    return StubTaggingProvider()
