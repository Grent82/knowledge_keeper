from apps.playback.providers.stub import StubSummaryProvider, StubTranscriptionProvider


def test_stub_transcription_provider_returns_segments():
    provider = StubTranscriptionProvider()

    result = provider.transcribe("demo.wav", language="de")

    assert result.full_text.startswith("[Stub transcript]")
    assert result.language_code == "de"
    assert len(result.segments) == 2
    assert result.segments[0].sequence_number == 1
    assert result.segments[0].start_seconds == 0.0


def test_stub_summary_provider_returns_summary_text():
    provider = StubSummaryProvider()

    result = provider.summarize("Transcript text for testing.", kind="detailed")

    assert result.startswith("[Stub detailed summary]")
    assert "Transcript text" in result
