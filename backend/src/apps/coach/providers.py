from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

from apps.accounts.models import User
from apps.playback.models import ArtifactStatus, TranscriptSegment

from .ports import RetrievalProvider, ScoredSegment
from .snippets import build_segment_snippet, extract_query_terms


class StubRetrievalProvider:
    """Deterministic local provider using simple content matching."""

    def retrieve_segments(self, query: str, owner: User, limit: int = 5) -> list[ScoredSegment]:
        terms = extract_query_terms(query)
        if not terms:
            return []
        queryset = TranscriptSegment.objects.filter(
            transcript__status=ArtifactStatus.READY,
            transcript__media_item__owner=owner,
        ).select_related("transcript__media_item")

        segments: list[ScoredSegment] = []
        minimum_distinct_matches = 1 if len(terms) == 1 else 2
        for segment in queryset:
            haystack = segment.content.lower()
            matched_terms = [term for term in terms if term in haystack]
            score = sum(haystack.count(term) for term in matched_terms)
            if score <= 0 or len(set(matched_terms)) < minimum_distinct_matches:
                continue
            segments.append(
                ScoredSegment(
                    segment_id=segment.id,
                    transcript_id=segment.transcript_id,
                    media_item_id=segment.transcript.media_item_id,
                    content=segment.content,
                    snippet=build_segment_snippet(segment, terms),
                    score=float(score),
                    start_seconds=segment.start_seconds,
                )
            )

        segments.sort(key=lambda item: (-item.score, item.segment_id))
        return segments[:limit]


class PostgresFTSRetrievalProvider:
    """PostgreSQL full-text search implementation over transcript segments."""

    def retrieve_segments(self, query: str, owner: User, limit: int = 5) -> list[ScoredSegment]:
        terms = extract_query_terms(query)
        if not terms:
            return []

        normalized_query = " ".join(terms)
        search_vector = SearchVector("content", config="simple")
        search_query = SearchQuery(normalized_query, config="simple")
        minimum_rank = 0.05 if len(terms) == 1 else 0.01
        queryset = (
            TranscriptSegment.objects.filter(
                transcript__status=ArtifactStatus.READY,
                transcript__media_item__owner=owner,
            )
            .annotate(rank=SearchRank(search_vector, search_query))
            .filter(rank__gte=minimum_rank)
            .select_related("transcript__media_item")
            .order_by("-rank", "id")[:limit]
        )
        return [
            ScoredSegment(
                segment_id=segment.id,
                transcript_id=segment.transcript_id,
                media_item_id=segment.transcript.media_item_id,
                content=segment.content,
                snippet=build_segment_snippet(segment, terms),
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
