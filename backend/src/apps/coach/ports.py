from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from apps.accounts.models import User


@dataclass
class ScoredSegment:
    segment_id: int
    transcript_id: int
    media_item_id: int
    content: str
    score: float
    start_seconds: Decimal | None = None


class RetrievalProvider(Protocol):
    def retrieve_segments(self, query: str, owner: User, limit: int = 5) -> list[ScoredSegment]: ...


class ChatProvider(Protocol):
    def generate_answer(
        self, question: str, history: list[dict[str, str]], segments: list[ScoredSegment]
    ) -> str: ...
