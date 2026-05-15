import logging

from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAICompatibleEmbeddingProvider:
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

    def embed_text(self, text: str) -> list[float]:
        response = self.client.embeddings.create(input=text, model=self.model)
        return response.data[0].embedding
