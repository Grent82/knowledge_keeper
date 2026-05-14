import logging

from openai import OpenAI

from ..ports import SummaryProvider

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are a helpful assistant that creates concise summaries of audio transcripts. "
    "Respond only with the summary text, no preamble."
)

_KIND_INSTRUCTIONS = {
    "short": "Write a short summary (2-4 sentences) capturing the key points.",
    "detailed": "Write a detailed summary (1-2 paragraphs) covering the main topics and insights.",
    "bullet": "Write a bullet-point summary with the 5-7 most important takeaways.",
}


def _first_non_empty_text(*values: object) -> str:
    for value in values:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
    return ""


def _extract_summary_text(response: object) -> str:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return ""

    first_choice = choices[0]
    message = getattr(first_choice, "message", None)
    message_extra = getattr(message, "model_extra", {}) or {}
    choice_extra = getattr(first_choice, "model_extra", {}) or {}

    return _first_non_empty_text(
        getattr(message, "content", None),
        getattr(first_choice, "text", None),
        message_extra.get("content"),
        choice_extra.get("text"),
    )


class OpenAICompatibleSummaryProvider:
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def summarize(self, transcript_text: str, kind: str = "short") -> str:
        instruction = _KIND_INSTRUCTIONS.get(kind, _KIND_INSTRUCTIONS["short"])
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"{instruction}\n"
                        "Write in the same language as the transcript.\n\n"
                        f"Transcript:\n{transcript_text}"
                    ),
                },
            ],
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            max_tokens=1024,
            temperature=0.3,
        )
        extracted = _extract_summary_text(response)
        if extracted:
            return extracted

        choices = getattr(response, "choices", None) or []
        first_choice = choices[0] if choices else None
        message = getattr(first_choice, "message", None)
        logger.warning(
            "Summary provider returned empty text",
            extra={
                "kind": kind,
                "finish_reason": getattr(first_choice, "finish_reason", None),
                "refusal": getattr(message, "refusal", None),
                "message_extra_keys": sorted(
                    (getattr(message, "model_extra", {}) or {}).keys()
                ),
                "choice_extra_keys": sorted(
                    (getattr(first_choice, "model_extra", {}) or {}).keys()
                ),
            },
        )
        return ""


def make_summary_provider(
    base_url: str, api_key: str, model: str
) -> SummaryProvider:
    return OpenAICompatibleSummaryProvider(base_url=base_url, api_key=api_key, model=model)
