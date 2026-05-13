import re

from apps.playback.models import TranscriptSegment

_STOPWORDS = {
    "aber",
    "auch",
    "bin",
    "bist",
    "damit",
    "dann",
    "dass",
    "dein",
    "deine",
    "deinem",
    "deiner",
    "dem",
    "den",
    "der",
    "des",
    "die",
    "dir",
    "doch",
    "eine",
    "einer",
    "eines",
    "einfach",
    "euch",
    "fuer",
    "habe",
    "hast",
    "hat",
    "hier",
    "ich",
    "ihr",
    "ihre",
    "ihren",
    "ihres",
    "ist",
    "kann",
    "kannst",
    "los",
    "mein",
    "meine",
    "meinem",
    "meiner",
    "mich",
    "mir",
    "mit",
    "nicht",
    "noch",
    "oder",
    "schon",
    "sich",
    "sie",
    "sind",
    "und",
    "uns",
    "unter",
    "vom",
    "von",
    "warum",
    "was",
    "weil",
    "werde",
    "wie",
    "wieder",
    "wir",
    "wird",
    "wo",
    "zu",
}

_TOKEN_RE = re.compile(r"[A-Za-z0-9ÄÖÜäöüß]+")


def extract_query_terms(query: str) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for token in _TOKEN_RE.findall(query.lower()):
        if len(token) <= 3 or token in _STOPWORDS:
            continue
        if token in seen:
            continue
        seen.add(token)
        terms.append(token)
    return terms


def collapse_whitespace(value: str) -> str:
    return " ".join(value.split())


def build_segment_snippet(
    segment: TranscriptSegment,
    query_terms: list[str],
    neighbor_window: int = 1,
    max_chars: int = 220,
) -> str:
    neighbor_segments = list(
        TranscriptSegment.objects.filter(
            transcript_id=segment.transcript_id,
            sequence_number__gte=max(1, segment.sequence_number - neighbor_window),
            sequence_number__lte=segment.sequence_number + neighbor_window,
        ).order_by("sequence_number")
    )

    combined = collapse_whitespace(" ".join(item.content for item in neighbor_segments))
    if len(combined) <= max_chars:
        return combined

    lowered = combined.lower()
    first_hit = next((lowered.find(term) for term in query_terms if term in lowered), -1)

    if first_hit < 0:
        current = collapse_whitespace(segment.content)
        if len(current) <= max_chars:
            return current
        return f"{current[: max_chars - 1].rstrip()}…"

    start = max(0, first_hit - 70)
    end = min(len(combined), start + max_chars)
    snippet = combined[start:end].strip()
    if start > 0:
        snippet = f"…{snippet}"
    if end < len(combined):
        snippet = f"{snippet.rstrip()}…"
    return snippet
