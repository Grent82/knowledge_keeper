import hashlib


class StubEmbeddingProvider:
    DIM = 16

    def embed_text(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        raw = [(byte / 127.5) - 1.0 for byte in digest[: self.DIM]]
        norm = sum(value**2 for value in raw) ** 0.5 or 1.0
        return [value / norm for value in raw]
