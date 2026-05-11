"""Parse WebVTT subtitle files into TranscriptionResult."""
import re

from ..ports import SegmentResult, TranscriptionResult

_TIMESTAMP_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})"
)
_TAG_RE = re.compile(r"<[^>]+>")


def _to_seconds(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse_vtt(vtt_text: str) -> TranscriptionResult:
    segments = []
    sequence = 0
    lines = vtt_text.splitlines()
    i = 0

    while i < len(lines):
        m = _TIMESTAMP_RE.match(lines[i].strip())
        if m:
            start = _to_seconds(m.group(1), m.group(2), m.group(3), m.group(4))
            end = _to_seconds(m.group(5), m.group(6), m.group(7), m.group(8))
            i += 1
            text_parts = []
            while i < len(lines) and lines[i].strip():
                text_parts.append(_TAG_RE.sub("", lines[i]).strip())
                i += 1
            text = " ".join(t for t in text_parts if t)
            if text:
                sequence += 1
                segments.append(
                    SegmentResult(
                        sequence_number=sequence,
                        content=text,
                        start_seconds=start,
                        end_seconds=end,
                    )
                )
        else:
            i += 1

    # Deduplicate consecutive identical lines (YouTube repeats lines in rolling captions)
    deduped = []
    prev = None
    for seg in segments:
        if seg.content != prev:
            deduped.append(seg)
            prev = seg.content

    for idx, seg in enumerate(deduped, start=1):
        seg.sequence_number = idx

    full_text = " ".join(seg.content for seg in deduped)
    return TranscriptionResult(full_text=full_text, segments=deduped)
