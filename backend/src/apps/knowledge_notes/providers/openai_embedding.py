import json
import os
import urllib.request


class OpenAICompatibleEmbeddingProvider:
    def __init__(self) -> None:
        self.api_url = os.getenv("EMBEDDING_API_URL", "https://api.openai.com/v1/embeddings")
        self.api_key = os.getenv("EMBEDDING_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        self.model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    def embed_text(self, text: str) -> list[float]:
        payload = json.dumps({"input": text, "model": self.model}).encode()
        req = urllib.request.Request(
            self.api_url,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        return data["data"][0]["embedding"]
