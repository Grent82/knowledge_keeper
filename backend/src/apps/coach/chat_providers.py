from typing import Any, cast

from openai import OpenAI

from .ports import ChatProvider, CoachAnswer, ScoredSegment

_SYSTEM_PROMPT = (
    "Du bist ein vorsichtiger, quellenbasierter Coach fuer die persoenliche Wissenssammlung des "
    "Nutzers. Antworte in der Sprache der Frage. Nutze nur den bereitgestellten Kontext. "
    "Du bist keine therapeutische oder medizinische Autoritaet. "
    "Bei sensiblen Fragen zu Angst, Krise, Selbstwert oder Leiden gib keine Heilungs-, Sofort- "
    "oder Gewissheitsversprechen. Formuliere Grenzen offen und bleibe bei vorsichtiger "
    "Orientierung. "
    "Wenn der Kontext schwach oder leer ist, sage das klar und erfinde keine Quellen."
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
        lines.append(f"{header} {segment.snippet}")
    return "\n".join(lines)


def _is_sensitive_question(question: str) -> bool:
    lowered = question.lower()
    return any(
        term in lowered
        for term in (
            "angst",
            "aengst",
            "panik",
            "depress",
            "wertlos",
            "ueberfordert",
            "überfordert",
            "krise",
            "suizid",
            "selbsthass",
        )
    )


class OpenAICompatibleChatProvider:
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def generate_answer(
        self, question: str, history: list[dict[str, str]], segments: list[ScoredSegment]
    ) -> CoachAnswer:
        messages: list[dict[str, str]] = [{"role": "system", "content": _SYSTEM_PROMPT}]
        messages.extend(history)
        sensitivity_note = (
            "\n\nZusatzregel fuer diese Frage: Formuliere besonders vorsichtig, "
            "nicht-therapeutisch und ohne Sofortloesungsversprechen."
            if _is_sensitive_question(question)
            else ""
        )
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Frage:\n{question}\n\n"
                    f"Kontext aus der Wissensbasis:\n{_build_context(segments)}"
                    f"{sensitivity_note}"
                ),
            }
        )
        response = self.client.chat.completions.create(
            model=self.model,
            messages=cast(Any, messages),
            max_tokens=512,
            temperature=0.3,
        )
        return CoachAnswer(
            answer=(response.choices[0].message.content or "").strip(),
            mode="grounded_answer",
        )


class StubChatProvider:
    def generate_answer(
        self, question: str, history: list[dict[str, str]], segments: list[ScoredSegment]
    ) -> CoachAnswer:
        if not segments:
            if _is_sensitive_question(question):
                return CoachAnswer(
                    answer=(
                        "Ich kann dir dazu keine therapeutische Antwort geben und habe in deiner "
                        "Sammlung gerade keine passenden Quellen gefunden."
                    ),
                    mode="sources_only",
                )
            return CoachAnswer(
                answer="Ich habe aktuell keine passenden Stellen in deiner Wissensbasis gefunden.",
                mode="sources_only",
            )
        if _is_sensitive_question(question):
            return CoachAnswer(
                answer=(
                    "Ich kann dir dazu keine therapeutische Antwort geben. "
                    "Ich zeige dir aber passende Quellen aus deiner Sammlung, die dir Orientierung "
                    "geben koennen."
                ),
                mode="sources_only",
            )
        return CoachAnswer(
            answer=(
                "Ich bin gerade im quellenbasierten Modus und zeige dir passende Stellen aus "
                "deiner Sammlung statt einer ausformulierten Coach-Antwort."
            ),
            mode="sources_only",
        )


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
