from unittest.mock import patch

import pytest
from django.test import override_settings

from apps.accounts.models import User, UserRole
from apps.media_library.models import ExternalSource, MediaAsset, MediaItem, MediaType
from apps.playback.models import (
    ArtifactStatus,
    Summary,
    Transcript,
    TranscriptProvider,
    TranscriptSegment,
)
from apps.playback.ports import SegmentResult, TranscriptionResult
from apps.playback.tasks import summarize_transcript, transcribe_media_item

pytestmark = pytest.mark.django_db


def _media_item_with_asset(username: str, title: str, media_type=MediaType.AUDIO) -> MediaItem:
    owner = User.objects.create_user(username=username, role=UserRole.OWNER)
    asset = MediaAsset.objects.create(storage_path="test/audio.mp3", created_by=owner)
    return MediaItem.objects.create(title=title, media_type=media_type, owner=owner, asset=asset)


def _media_item_with_external_source(
    username: str,
    title: str,
    source_url: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    media_type: str = MediaType.VIDEO,
) -> MediaItem:
    owner = User.objects.create_user(username=username, role=UserRole.OWNER)
    source = ExternalSource.objects.create(
        provider="youtube",
        source_url=source_url,
        title=title,
        created_by=owner,
    )
    return MediaItem.objects.create(
        title=title,
        media_type=media_type,
        owner=owner,
        external_source=source,
    )


@patch("apps.playback.tasks.summarize_transcript.delay")
@patch("apps.playback.tasks.get_transcription_provider")
def test_transcribe_media_item_creates_transcript_and_segments(
    mock_get_provider, mock_summarize_delay
):
    mock_provider = mock_get_provider.return_value
    mock_provider.transcribe.return_value = TranscriptionResult(
        full_text="Hello task world",
        segments=[
            SegmentResult(sequence_number=1, content="Hello", start_seconds=0.0, end_seconds=1.5),
            SegmentResult(
                sequence_number=2,
                content="task world",
                start_seconds=1.5,
                end_seconds=3.0,
            ),
        ],
        language_code="en",
    )
    media_item = _media_item_with_asset("owner-task-success", "Task Source")

    transcribe_media_item.run(media_item.id)

    transcript = Transcript.objects.get(media_item=media_item)
    assert transcript.status == ArtifactStatus.READY
    assert transcript.content == "Hello task world"
    assert transcript.language_code == "en"
    assert transcript.generated_at is not None
    assert list(transcript.segments.values_list("content", flat=True)) == ["Hello", "task world"]
    mock_summarize_delay.assert_called_once_with(transcript.id)


@patch("apps.playback.tasks.summarize_transcript.delay")
@patch("apps.playback.tasks.get_transcription_provider")
@patch("apps.playback.tasks._try_youtube_captions")
def test_transcribe_media_item_uses_youtube_captions_without_audio_fallback(
    mock_try_youtube_captions,
    mock_get_provider,
    mock_summarize_delay,
):
    mock_try_youtube_captions.return_value = TranscriptionResult(
        full_text="Caption transcript",
        segments=[
            SegmentResult(
                sequence_number=0,
                content="Caption transcript",
                start_seconds=0.0,
                end_seconds=2.0,
            ),
        ],
        language_code="de",
    )
    media_item = _media_item_with_external_source("owner-caption-success", "Caption Source")

    transcribe_media_item.run(media_item.id)

    transcript = Transcript.objects.get(media_item=media_item)
    assert transcript.status == ArtifactStatus.READY
    assert transcript.content == "Caption transcript"
    assert transcript.language_code == "de"
    assert list(transcript.segments.values_list("content", flat=True)) == ["Caption transcript"]
    mock_get_provider.return_value.transcribe.assert_not_called()
    mock_summarize_delay.assert_called_once_with(transcript.id)


@patch("apps.playback.tasks.summarize_transcript.delay")
@patch("apps.playback.tasks.get_transcription_provider")
@patch("apps.playback.tasks._resolve_audio_path")
@patch("apps.playback.tasks._try_youtube_captions")
def test_transcribe_media_item_falls_back_to_audio_when_captions_missing(
    mock_try_youtube_captions,
    mock_resolve_audio_path,
    mock_get_provider,
    mock_summarize_delay,
):
    mock_try_youtube_captions.return_value = None
    mock_resolve_audio_path.return_value = ("tmp/audio.mp3", None)
    mock_get_provider.return_value.transcribe.return_value = TranscriptionResult(
        full_text="Fallback transcript",
        segments=[
            SegmentResult(
                sequence_number=0,
                content="Fallback transcript",
                start_seconds=0.0,
                end_seconds=2.0,
            ),
        ],
        language_code="en",
    )
    media_item = _media_item_with_external_source("owner-caption-fallback", "Fallback Source")

    transcribe_media_item.run(media_item.id)

    transcript = Transcript.objects.get(media_item=media_item)
    assert transcript.status == ArtifactStatus.READY
    assert transcript.content == "Fallback transcript"
    mock_resolve_audio_path.assert_called_once_with(media_item)
    mock_get_provider.return_value.transcribe.assert_called_once_with("tmp/audio.mp3")
    mock_summarize_delay.assert_called_once_with(transcript.id)


@patch("apps.playback.tasks.summarize_transcript.delay")
@patch("apps.playback.tasks.get_transcription_provider")
@patch("apps.playback.tasks._resolve_audio_path")
@patch("apps.playback.tasks._try_youtube_captions")
def test_transcribe_media_item_falls_back_to_audio_when_caption_fetch_raises(
    mock_try_youtube_captions,
    mock_resolve_audio_path,
    mock_get_provider,
    mock_summarize_delay,
):
    mock_try_youtube_captions.side_effect = RuntimeError("caption lookup failed")
    mock_resolve_audio_path.return_value = ("tmp/audio.mp3", None)
    mock_get_provider.return_value.transcribe.return_value = TranscriptionResult(
        full_text="Recovered transcript",
        segments=[
            SegmentResult(
                sequence_number=0,
                content="Recovered transcript",
                start_seconds=0.0,
                end_seconds=2.0,
            ),
        ],
        language_code="en",
    )
    media_item = _media_item_with_external_source("owner-caption-error", "Caption Error Source")

    transcribe_media_item.run(media_item.id)

    transcript = Transcript.objects.get(media_item=media_item)
    assert transcript.status == ArtifactStatus.READY
    assert transcript.content == "Recovered transcript"
    mock_resolve_audio_path.assert_called_once_with(media_item)
    mock_get_provider.return_value.transcribe.assert_called_once_with("tmp/audio.mp3")
    mock_summarize_delay.assert_called_once_with(transcript.id)


@patch("apps.playback.tasks.summarize_transcript.delay")
@patch("apps.playback.tasks.get_transcription_provider")
def test_transcribe_media_item_idempotent(mock_get_provider, mock_summarize_delay):
    owner = User.objects.create_user(username="owner-task-idempotent", role=UserRole.OWNER)
    media_item = MediaItem.objects.create(
        title="Ready Source",
        media_type=MediaType.VIDEO,
        owner=owner,
    )
    transcript = Transcript.objects.create(
        media_item=media_item,
        status=ArtifactStatus.READY,
        content="Existing transcript",
        language_code="de",
    )
    TranscriptSegment.objects.create(
        transcript=transcript,
        sequence_number=1,
        content="Existing segment",
    )

    transcribe_media_item.run(media_item.id)

    transcript.refresh_from_db()
    assert transcript.status == ArtifactStatus.READY
    assert transcript.content == "Existing transcript"
    assert transcript.language_code == "de"
    assert TranscriptSegment.objects.filter(transcript=transcript).count() == 1
    mock_get_provider.return_value.transcribe.assert_not_called()
    mock_summarize_delay.assert_not_called()


@patch("apps.playback.tasks.transcribe_media_item.retry")
@patch("apps.playback.tasks.get_transcription_provider")
@patch("apps.playback.tasks._resolve_audio_path")
@patch("apps.playback.tasks._try_youtube_captions")
def test_transcribe_media_item_marks_drm_failures_without_retry(
    mock_try_youtube_captions,
    mock_resolve_audio_path,
    mock_get_provider,
    mock_retry,
):
    mock_try_youtube_captions.return_value = None
    mock_resolve_audio_path.side_effect = RuntimeError("This video is DRM protected")
    media_item = _media_item_with_external_source("owner-drm-failure", "DRM Source")

    transcribe_media_item.run(media_item.id)

    transcript = Transcript.objects.get(media_item=media_item)
    assert transcript.status == ArtifactStatus.FAILED
    assert "DRM-geschützt" in transcript.error_message
    mock_get_provider.return_value.transcribe.assert_not_called()
    mock_retry.assert_not_called()


@patch("apps.playback.tasks.transcribe_media_item.retry")
@patch(
    "apps.playback.tasks.get_transcription_provider",
)
def test_transcribe_media_item_failed_on_provider_error(mock_get_provider, mock_retry):
    mock_get_provider.return_value.transcribe.side_effect = RuntimeError("provider failed")
    media_item = _media_item_with_asset("owner-task-failure", "Broken Source")
    mock_retry.side_effect = RuntimeError("retry requested")

    with pytest.raises(RuntimeError, match="retry requested"):
        transcribe_media_item.run(media_item.id)

    transcript = Transcript.objects.get(media_item=media_item)
    assert transcript.status == ArtifactStatus.FAILED
    assert transcript.error_message == "provider failed"
    mock_get_provider.return_value.transcribe.assert_called_once()
    mock_retry.assert_called_once()


@patch("apps.playback.tasks.get_summary_provider")
@override_settings(SUMMARY_PROVIDER="openai_compatible")
def test_summarize_transcript_creates_summary(mock_get_provider):
    mock_get_provider.return_value.summarize.return_value = "Short summary"
    owner = User.objects.create_user(username="owner-summary-task", role=UserRole.OWNER)
    media_item = MediaItem.objects.create(
        title="Summary Source",
        media_type=MediaType.AUDIO,
        owner=owner,
    )
    transcript = Transcript.objects.create(
        media_item=media_item,
        status=ArtifactStatus.READY,
        content="Long transcript body",
    )

    summarize_transcript.run(transcript.id)

    summary = Summary.objects.get(media_item=media_item, transcript=transcript)
    assert summary.status == ArtifactStatus.READY
    assert summary.content == "Short summary"
    assert summary.provider == TranscriptProvider.OPENAI
    assert summary.generated_at is not None
    mock_get_provider.return_value.summarize.assert_called_once_with(
        "Long transcript body",
        kind="short",
    )


def test_summarize_transcript_skips_if_not_ready():
    owner = User.objects.create_user(username="owner-summary-skip", role=UserRole.OWNER)
    media_item = MediaItem.objects.create(
        title="Pending Source",
        media_type=MediaType.VIDEO,
        owner=owner,
    )
    transcript = Transcript.objects.create(
        media_item=media_item,
        status=ArtifactStatus.PENDING,
        content="Not ready",
    )

    summarize_transcript.run(transcript.id)

    assert not Summary.objects.filter(media_item=media_item, transcript=transcript).exists()


@patch("apps.playback.tasks.summarize_transcript.retry")
@patch("apps.playback.tasks.get_summary_provider")
@override_settings(SUMMARY_PROVIDER="openai_compatible")
def test_summarize_transcript_marks_empty_output_failed_without_retry(
    mock_get_provider, mock_retry
):
    mock_get_provider.return_value.summarize.return_value = "   "
    owner = User.objects.create_user(username="owner-summary-empty", role=UserRole.OWNER)
    media_item = MediaItem.objects.create(
        title="Empty Summary Source",
        media_type=MediaType.AUDIO,
        owner=owner,
    )
    transcript = Transcript.objects.create(
        media_item=media_item,
        status=ArtifactStatus.READY,
        content="Transcript body",
    )

    summarize_transcript.run(transcript.id, kind="detailed")

    summary = Summary.objects.get(media_item=media_item, transcript=transcript, kind="detailed")
    assert summary.status == ArtifactStatus.FAILED
    assert summary.provider == TranscriptProvider.OPENAI
    assert summary.error_message == "Summary provider returned empty content for kind 'detailed'."
    mock_retry.assert_not_called()
