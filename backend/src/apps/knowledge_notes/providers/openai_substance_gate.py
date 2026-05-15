import logging

from openai import OpenAI

logger = logging.getLogger(__name__)

_GATE_SYSTEM = (
    "Du bewertest Transkript-Abschnitte auf ihr Transformations-Potenzial. "
    "Antworte NUR mit einer einzelnen Ganzzahl zwischen 0 und 10. Keine anderen Zeichen."
)

_GATE_USER = (
    "Bewerte den folgenden Transkript-Abschnitt auf "
    "Transformations-Potenzial auf einer Skala von 0-10.\n"
    "10 = enthält mindestens eine Erkenntnis die das Leben des Lesers konkret "
    "verändern kann.\n"
    "0 = reine Inhalts-Beschreibung, Eigenwerbung, Smalltalk oder technische "
    "Details ohne Übertragbarkeit.\n"
    "Antworte NUR mit einer Ganzzahl.\n\nAbschnitt:\n{chunk}"
)


class OpenAICompatibleSubstanceGateProvider:
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

    def assess(self, text: str) -> int:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _GATE_SYSTEM},
                    {"role": "user", "content": _GATE_USER.format(chunk=text[:1500])},
                ],
                max_tokens=5,
                temperature=0,
            )
            raw = (response.choices[0].message.content or "").strip()
            return max(0, min(10, int(raw)))
        except (ValueError, Exception):
            logger.warning("Substance gate assessment failed; defaulting to 5")
            return 5
