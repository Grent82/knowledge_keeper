from types import SimpleNamespace

from apps.playback.providers.openai_compatible import OpenAICompatibleSummaryProvider
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


def test_openai_compatible_summary_provider_returns_message_content():
    provider = OpenAICompatibleSummaryProvider(
        base_url="https://example.invalid/v1",
        api_key="test-key",
        model="test-model",
    )
    provider.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **_: SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(
                                content="Detailed summary body",
                                model_extra={},
                            ),
                            model_extra={},
                        )
                    ]
                )
            )
        )
    )

    result = provider.summarize("Transcript text for testing.", kind="detailed")

    assert result == "Detailed summary body"


def test_openai_compatible_summary_provider_falls_back_to_choice_text():
    provider = OpenAICompatibleSummaryProvider(
        base_url="https://example.invalid/v1",
        api_key="test-key",
        model="test-model",
    )
    provider.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **_: SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(content=None, model_extra={}),
                            text="Bullet summary from legacy text field",
                            model_extra={},
                        )
                    ]
                )
            )
        )
    )

    result = provider.summarize("Transcript text for testing.", kind="bullet")

    assert result == "Bullet summary from legacy text field"
