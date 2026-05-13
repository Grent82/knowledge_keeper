from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

from apps.accounts.models import User
from apps.playback.models import ArtifactStatus, TranscriptSegment

from .ports import RetrievalProvider, ScoredSegment


class StubRetrievalProvider:
    """Deterministic local provider using simple content matching."""

    def retrieve_segments(self, query: str, owner: User, limit: int = 5) -> list[ScoredSegment]:
        terms = [term.strip().lower() for term in query.split() if term.strip()]
        queryset = TranscriptSegment.objects.filter(
            transcript__status=ArtifactStatus.READY,
            transcript__media_item__owner=owner,
        ).select_related("transcript__media_item")

        segments: list[ScoredSegment] = []
        for segment in queryset:
            haystack = segment.content.lower()
            score = sum(haystack.count(term) for term in terms)
            if score <= 0:
                continue
            segments.append(
                ScoredSegment(
                    segment_id=segment.id,
                    transcript_id=segment.transcript_id,
                    media_item_id=segment.transcript.media_item_id,
                    content=segment.content,
                    score=float(score),
                    start_seconds=segment.start_seconds,
                )
            )

        segments.sort(key=lambda item: (-item.score, item.segment_id))
        return segments[:limit]


class PostgresFTSRetrievalProvider:
    """PostgreSQL full-text search implementation over transcript segments."""

    def retrieve_segments(self, query: str, owner: User, limit: int = 5) -> list[ScoredSegment]:
        search_vector = SearchVector("content", config="simple")
        search_query = SearchQuery(query, config="simple")
        queryset = (
            TranscriptSegment.objects.filter(
                transcript__status=ArtifactStatus.READY,
                transcript__media_item__owner=owner,
            )
            .annotate(rank=SearchRank(search_vector, search_query))
            .filter(rank__gt=0)
            .select_related("transcript__media_item")
            .order_by("-rank", "id")[:limit]
        )
        return [
            ScoredSegment(
                segment_id=segment.id,
                transcript_id=segment.transcript_id,
                media_item_id=segment.transcript.media_item_id,
                content=segment.content,
                score=float(segment.rank),
                start_seconds=segment.start_seconds,
            )
            for segment in queryset
        ]


def get_retrieval_provider() -> RetrievalProvider:
    provider = getattr(settings, "RETRIEVAL_PROVIDER", "stub")

    if provider == "postgres_fts":
        return PostgresFTSRetrievalProvider()

    return StubRetrievalProvider()
