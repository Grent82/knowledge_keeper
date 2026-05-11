from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class SegmentResult:
    sequence_number: int
    content: str
    start_seconds: float | None = None
    end_seconds: float | None = None


@dataclass
class TranscriptionResult:
    full_text: str
    segments: list[SegmentResult] = field(default_factory=list)
    language_code: str = ""


class TranscriptionProvider(Protocol):
    def transcribe(self, audio_path: str, language: str = "") -> TranscriptionResult: ...


class SummaryProvider(Protocol):
    def summarize(self, transcript_text: str, kind: str = "short") -> str: ...
