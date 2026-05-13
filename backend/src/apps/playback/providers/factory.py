from django.conf import settings

from ..ports import SummaryProvider, TranscriptionProvider


def get_transcription_provider() -> TranscriptionProvider:
    provider = getattr(settings, "TRANSCRIPTION_PROVIDER", "stub")

    if provider == "faster_whisper":
        from .faster_whisper_provider import make_faster_whisper_provider

        return make_faster_whisper_provider()

    from .stub import StubTranscriptionProvider

    return StubTranscriptionProvider()


def get_summary_provider() -> SummaryProvider:
    provider = getattr(settings, "SUMMARY_PROVIDER", "stub")

    if provider == "openai_compatible":
        from .openai_compatible import make_summary_provider

        return make_summary_provider(
            base_url=settings.AI_HUB_BASE_URL,
            api_key=settings.AI_HUB_API_KEY,
            model=settings.AI_HUB_MODEL,
        )

    from .stub import StubSummaryProvider

    return StubSummaryProvider()


def get_summary_provider_label() -> str:
    provider = getattr(settings, "SUMMARY_PROVIDER", "stub")

    if provider == "openai_compatible":
        return "openai"
    if provider == "stub":
        return "local"
    return "other"
