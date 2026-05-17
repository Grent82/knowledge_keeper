from __future__ import annotations

import json
import logging

from openai import OpenAI

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Du bewertest nur, wie stark Wissensnotizen konzeptuell zusammengehoeren. "
    "Antworte nur mit gueltigem JSON."
)


class OpenAICompatibleLinkReranker:
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self._base_url = base_url
        self._api_key = api_key
        self.model = model
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(base_url=self._base_url, api_key=self._api_key)
        return self._client

    def rerank(
        self,
        anchor_text: str,
        candidates: list[dict[str, str | float | int]],
    ) -> dict[int, float]:
        if not candidates:
            return {}
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "anchor_text": anchor_text,
                            "candidates": candidates,
                            "task": (
                                "Gib ein JSON-Objekt mit dem Schluessel 'scores' zurueck. "
                                "Der Wert ist ein Array von Objekten mit 'id' und 'score' "
                                "(0.0 bis 1.0). Bewerte nur die inhaltliche Naehe."
                            ),
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        )
        raw_content = response.choices[0].message.content or "{}"
        payload = json.loads(raw_content)
        scores = payload.get("scores", [])
        result: dict[int, float] = {}
        for item in scores:
            try:
                result[int(item["id"])] = float(item["score"])
            except (KeyError, TypeError, ValueError):
                continue
        return result
