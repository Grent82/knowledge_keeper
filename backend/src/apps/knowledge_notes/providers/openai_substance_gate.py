import json
import os
import urllib.request

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
    def __init__(self) -> None:
        self.api_url = os.getenv("NOTE_API_URL", "https://api.openai.com/v1/chat/completions")
        self.api_key = os.getenv("NOTE_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        self.model = os.getenv("NOTE_MODEL", "gpt-4o-mini")

    def assess(self, text: str) -> int:
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": _GATE_SYSTEM},
                    {"role": "user", "content": _GATE_USER.format(chunk=text[:1500])},
                ],
                "max_tokens": 5,
                "temperature": 0,
            }
        ).encode()
        req = urllib.request.Request(
            self.api_url,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        raw = data["choices"][0]["message"]["content"].strip()
        try:
            score = int(raw)
            return max(0, min(10, score))
        except ValueError:
            return 5
