import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole
from apps.media_library.models import MediaItem, MediaType
from apps.playback.models import ArtifactStatus, PlaybackProgress, Summary, Transcript

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
