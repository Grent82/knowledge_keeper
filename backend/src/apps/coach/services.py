from apps.accounts.models import User

from .ports import ScoredSegment
from .providers import get_retrieval_provider


def retrieve_segments(query: str, owner: User, limit: int = 5) -> list[ScoredSegment]:
    normalized_query = query.strip()
    if not normalized_query or limit <= 0:
        return []

    return get_retrieval_provider().retrieve_segments(normalized_query, owner=owner, limit=limit)
