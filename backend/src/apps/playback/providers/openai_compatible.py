from openai import OpenAI

from ..ports import SummaryProvider

_SYSTEM_PROMPT = (
    "You are a helpful assistant that creates concise summaries of audio transcripts. "
    "Respond only with the summary text, no preamble."
)

_KIND_INSTRUCTIONS = {
    "short": "Write a short summary (2-4 sentences) capturing the key points.",
    "detailed": "Write a detailed summary (1-2 paragraphs) covering the main topics and insights.",
    "bullet": "Write a bullet-point summary with the 5-7 most important takeaways.",
}


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
                    "content": f"{instruction}\n\nTranscript:\n{transcript_text}",
                },
            ],
            max_tokens=1024,
            temperature=0.3,
        )
        return response.choices[0].message.content or ""


def make_summary_provider(
    base_url: str, api_key: str, model: str
) -> SummaryProvider:
    return OpenAICompatibleSummaryProvider(base_url=base_url, api_key=api_key, model=model)
