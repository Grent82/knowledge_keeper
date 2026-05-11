from ..ports import SegmentResult, SummaryProvider, TranscriptionProvider, TranscriptionResult


class StubTranscriptionProvider:
    def transcribe(self, audio_path: str, language: str = "") -> TranscriptionResult:
        return TranscriptionResult(
            full_text="[Stub transcript] This is a placeholder transcript.",
            segments=[
                SegmentResult(
                    sequence_number=1,
                    content="[Stub transcript]",
                    start_seconds=0.0,
                    end_seconds=2.0,
                ),
                SegmentResult(
                    sequence_number=2,
                    content="This is a placeholder transcript.",
                    start_seconds=2.0,
                    end_seconds=5.0,
                ),
            ],
            language_code=language or "en",
        )


class StubSummaryProvider:
    def summarize(self, transcript_text: str, kind: str = "short") -> str:
        return f"[Stub {kind} summary] {transcript_text[:100]}..."


transcription_provider: TranscriptionProvider = StubTranscriptionProvider()
summary_provider: SummaryProvider = StubSummaryProvider()
