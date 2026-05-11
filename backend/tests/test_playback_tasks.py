from unittest.mock import patch

import pytest

from apps.accounts.models import User, UserRole
from apps.media_library.models import MediaAsset, MediaItem, MediaType
from apps.playback.models import ArtifactStatus, Summary, Transcript, TranscriptSegment
from apps.playback.ports import SegmentResult, TranscriptionResult
from apps.playback.tasks import summarize_transcript, transcribe_media_item

pytestmark = pytest.mark.django_db


def _media_item_with_asset(username: str, title: str, media_type=MediaType.AUDIO) -> MediaItem:
    owner = User.objects.create_user(username=username, role=UserRole.OWNER)
    asset = MediaAsset.objects.create(storage_path="test/audio.mp3", created_by=owner)
    return MediaItem.objects.create(title=title, media_type=media_type, owner=owner, asset=asset)


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
    assert summary.generated_at is not None
    mock_get_provider.return_value.summarize.assert_called_once_with("Long transcript body", kind="short")


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
