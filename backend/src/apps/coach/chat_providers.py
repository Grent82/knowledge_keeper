from typing import Any, cast

from openai import OpenAI

from .ports import ChatProvider, ScoredSegment

_SYSTEM_PROMPT = (
    "Du bist ein empathischer, direkter, transformativer Coach. "
    "Antworte in der Sprache der Frage. Nutze nur den bereitgestellten Kontext. "
    "Wenn kein Kontext vorhanden ist, sage das offen und erfinde keine Quellen."
)


def _build_context(segments: list[ScoredSegment]) -> str:
    if not segments:
        return "Kein passender Kontext aus der Wissensbasis gefunden."

    lines: list[str] = []
    for segment in segments:
        header = (
            f"[segment:{segment.segment_id} media:{segment.media_item_id} "
            f"start:{segment.start_seconds}]"
        )
        lines.append(f"{header} {segment.content}")
    return "\n".join(lines)


class OpenAICompatibleChatProvider:
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def generate_answer(
        self, question: str, history: list[dict[str, str]], segments: list[ScoredSegment]
    ) -> str:
        messages: list[dict[str, str]] = [{"role": "system", "content": _SYSTEM_PROMPT}]
        messages.extend(history)
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Frage:\n{question}\n\n"
                    f"Kontext aus der Wissensbasis:\n{_build_context(segments)}"
                ),
            }
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=cast(Any, messages),
            max_tokens=512,
            temperature=0.3,
        )
        return (response.choices[0].message.content or "").strip()


class StubChatProvider:
    def generate_answer(
        self, question: str, history: list[dict[str, str]], segments: list[ScoredSegment]
    ) -> str:
        if not segments:
            return "Ich habe aktuell keine passenden Stellen in deiner Wissensbasis gefunden."
        return f"[Stub Coach] {question}"


def get_chat_provider() -> ChatProvider:
    from django.conf import settings

    provider = getattr(settings, "CHAT_PROVIDER", "stub")
    if provider == "openai_compatible":
        return OpenAICompatibleChatProvider(
            base_url=settings.AI_HUB_BASE_URL,
            api_key=settings.AI_HUB_API_KEY,
            model=settings.AI_HUB_MODEL,
        )
    return StubChatProvider()
