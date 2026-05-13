from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.media_library.models import MediaItem, MediaType
from apps.playback.models import (
    ArtifactStatus,
    PlaybackProgress,
    PlaybackStatus,
    Summary,
    SummaryKind,
    Transcript,
    TranscriptProvider,
    TranscriptSegment,
)
from apps.playback.tasks import summarize_transcript

pytestmark = pytest.mark.django_db


def test_playback_progress_is_unique_per_user_and_media_item():
    owner = User.objects.create_user(username="owner-progress")
    item = MediaItem.objects.create(
        title="Audio Progress",
        media_type=MediaType.AUDIO,
        owner=owner,
    )
    PlaybackProgress.objects.create(user=owner, media_item=item, status=PlaybackStatus.IN_PROGRESS)

    duplicate = PlaybackProgress(user=owner, media_item=item)

    with pytest.raises(ValidationError):
        duplicate.full_clean(validate_constraints=True)


def test_transcript_can_store_segments():
    owner = User.objects.create_user(username="owner-transcript")
    item = MediaItem.objects.create(
        title="Transcript Source",
        media_type=MediaType.VIDEO,
        owner=owner,
    )
    transcript = Transcript.objects.create(
        media_item=item,
        status=ArtifactStatus.READY,
        provider=TranscriptProvider.LOCAL,
        language_code="en",
        content="Hello world",
    )
    first = TranscriptSegment.objects.create(
        transcript=transcript,
        sequence_number=1,
        start_seconds=0,
        end_seconds=4.2,
        content="Hello",
    )
    second = TranscriptSegment.objects.create(
        transcript=transcript,
        sequence_number=2,
        start_seconds=4.2,
        end_seconds=8.4,
        content="world",
    )

    assert list(transcript.segments.all()) == [first, second]


def test_summary_can_reference_transcript():
    owner = User.objects.create_user(username="owner-summary")
    item = MediaItem.objects.create(
        title="Summary Source",
        media_type=MediaType.AUDIO,
        owner=owner,
    )
    transcript = Transcript.objects.create(
        media_item=item,
        status=ArtifactStatus.READY,
        provider=TranscriptProvider.OPENAI,
        content="Long transcript",
    )

    summary = Summary.objects.create(
        media_item=item,
        transcript=transcript,
        status=ArtifactStatus.READY,
        kind=SummaryKind.DETAILED,
        provider=TranscriptProvider.OPENAI,
        content="Detailed summary",
    )

    assert summary.transcript == transcript


@patch("apps.playback.tasks.get_summary_provider")
def test_summarize_transcript_overwrites_empty_ready_summary(mock_get_summary_provider):
    owner = User.objects.create_user(username="owner-empty-ready-task")
    item = MediaItem.objects.create(
        title="Summary Retry Source",
        media_type=MediaType.AUDIO,
        owner=owner,
    )
    transcript = Transcript.objects.create(
        media_item=item,
        status=ArtifactStatus.READY,
        provider=TranscriptProvider.LOCAL,
        content="Transcript content for regeneration.",
    )
    summary = Summary.objects.create(
        media_item=item,
        transcript=transcript,
        status=ArtifactStatus.READY,
        kind=SummaryKind.BULLET,
        provider=TranscriptProvider.LOCAL,
        content="",
        markdown_content="",
    )
    mock_get_summary_provider.return_value.summarize.return_value = "Recovered bullet summary"

    summarize_transcript(transcript.id, kind=SummaryKind.BULLET)

    summary.refresh_from_db()
    assert summary.status == ArtifactStatus.READY
    assert summary.content == "Recovered bullet summary"
    mock_get_summary_provider.return_value.summarize.assert_called_once_with(
        transcript.content,
        kind=SummaryKind.BULLET,
    )


@patch("apps.playback.tasks.get_summary_provider")
def test_summarize_transcript_marks_empty_provider_output_as_failed(mock_get_summary_provider):
    owner = User.objects.create_user(username="owner-empty-provider-output")
    item = MediaItem.objects.create(
        title="Summary Empty Output Source",
        media_type=MediaType.AUDIO,
        owner=owner,
    )
    transcript = Transcript.objects.create(
        media_item=item,
        status=ArtifactStatus.READY,
        provider=TranscriptProvider.LOCAL,
        content="Transcript content for empty output.",
    )
    mock_get_summary_provider.return_value.summarize.return_value = "   "

    summarize_transcript(transcript.id, kind=SummaryKind.DETAILED)

    summary = Summary.objects.get(
        media_item=item,
        transcript=transcript,
        kind=SummaryKind.DETAILED,
    )
    assert summary.status == ArtifactStatus.FAILED
    assert "empty" in summary.error_message.lower()
