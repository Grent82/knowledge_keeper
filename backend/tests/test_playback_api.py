import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole
from apps.media_library.models import MediaItem, MediaType
from apps.playback.models import (
    ArtifactStatus,
    PlaybackProgress,
    Summary,
    Transcript,
    TranscriptSegment,
)

pytestmark = pytest.mark.django_db


def test_user_can_create_own_playback_progress():
    owner = User.objects.create_user(username="owner-progress-api", password="secret")
    item = MediaItem.objects.create(title="Track", media_type=MediaType.AUDIO, owner=owner)
    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.post(
        "/api/playback/progress",
        {
            "media_item": item.id,
            "status": "in_progress",
            "position_seconds": 42,
            "progress_percent": "11.50",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["user"] == owner.id
    assert PlaybackProgress.objects.filter(user=owner, media_item=item).exists()


def test_owner_can_create_transcript_and_summary():
    owner = User.objects.create_user(
        username="owner-artifact",
        password="secret",
        role=UserRole.OWNER,
    )
    item = MediaItem.objects.create(title="Artifact Item", media_type=MediaType.VIDEO, owner=owner)
    client = APIClient()
    client.force_authenticate(user=owner)

    transcript_response = client.post(
        "/api/playback/transcripts",
        {
            "media_item": item.id,
            "status": "processing",
            "provider": "openai",
        },
        format="json",
    )
    summary_response = client.post(
        "/api/playback/summaries",
        {
            "media_item": item.id,
            "status": "pending",
            "kind": "short",
            "provider": "openai",
        },
        format="json",
    )

    assert transcript_response.status_code == 201
    assert summary_response.status_code == 201
    assert Transcript.objects.filter(media_item=item, status=ArtifactStatus.PROCESSING).exists()
    assert Summary.objects.filter(media_item=item, status=ArtifactStatus.PENDING).exists()


def test_transcript_and_summary_list_can_filter_by_media_item():
    owner = User.objects.create_user(
        username="owner-artifact-filter",
        password="secret",
        role=UserRole.OWNER,
    )
    first_item = MediaItem.objects.create(
        title="First Item",
        media_type=MediaType.AUDIO,
        owner=owner,
    )
    second_item = MediaItem.objects.create(
        title="Second Item",
        media_type=MediaType.VIDEO,
        owner=owner,
    )
    Transcript.objects.create(
        media_item=first_item,
        status=ArtifactStatus.READY,
        provider="local",
    )
    Transcript.objects.create(
        media_item=second_item,
        status=ArtifactStatus.FAILED,
        provider="other",
    )
    Summary.objects.create(media_item=first_item, status=ArtifactStatus.PENDING, kind="short")
    Summary.objects.create(media_item=second_item, status=ArtifactStatus.READY, kind="detailed")
    client = APIClient()
    client.force_authenticate(user=owner)

    transcript_response = client.get(f"/api/playback/transcripts?media_item={first_item.id}")
    summary_response = client.get(f"/api/playback/summaries?media_item={second_item.id}")

    assert transcript_response.status_code == 200
    assert [entry["media_item"] for entry in transcript_response.data] == [first_item.id]
    assert summary_response.status_code == 200
    assert [entry["media_item"] for entry in summary_response.data] == [second_item.id]


def test_owner_can_list_segments_for_a_specific_transcript():
    owner = User.objects.create_user(
        username="owner-segments",
        password="secret",
        role=UserRole.OWNER,
    )
    first_item = MediaItem.objects.create(
        title="Segment Item",
        media_type=MediaType.AUDIO,
        owner=owner,
    )
    second_item = MediaItem.objects.create(
        title="Other Segment Item",
        media_type=MediaType.AUDIO,
        owner=owner,
    )
    transcript = Transcript.objects.create(media_item=first_item, status=ArtifactStatus.READY)
    other_transcript = Transcript.objects.create(
        media_item=second_item,
        status=ArtifactStatus.READY,
    )
    TranscriptSegment.objects.create(
        transcript=transcript,
        sequence_number=2,
        content="Second",
    )
    TranscriptSegment.objects.create(
        transcript=transcript,
        sequence_number=1,
        content="First",
    )
    TranscriptSegment.objects.create(
        transcript=other_transcript,
        sequence_number=1,
        content="Other",
    )
    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.get(f"/api/playback/segments?transcript={transcript.id}")

    assert response.status_code == 200
    assert [entry["sequence_number"] for entry in response.data] == [1, 2]
    assert [entry["transcript"] for entry in response.data] == [transcript.id, transcript.id]
