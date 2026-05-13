import pytest
from django.db import connection

from apps.accounts.models import User, UserRole
from apps.media_library.models import MediaAsset, MediaItem, MediaType
from apps.playback.models import ArtifactStatus, Transcript, TranscriptSegment

pytestmark = pytest.mark.django_db


def _owner(username: str) -> User:
    return User.objects.create_user(username=username, role=UserRole.OWNER)


def _media_item(owner: User, title: str) -> MediaItem:
    asset = MediaAsset.objects.create(storage_path=f"{title}.mp3", created_by=owner)
    return MediaItem.objects.create(
        title=title,
        media_type=MediaType.AUDIO,
        owner=owner,
        asset=asset,
    )


def _transcript_with_segments(media_item: MediaItem, segments: list[str]) -> Transcript:
    transcript = Transcript.objects.create(
        media_item=media_item,
        status=ArtifactStatus.READY,
        content=" ".join(segments),
        language_code="de",
    )
    TranscriptSegment.objects.bulk_create(
        [
            TranscriptSegment(
                transcript=transcript,
                sequence_number=index,
                content=content,
                start_seconds=float(index * 10),
            )
            for index, content in enumerate(segments, start=1)
        ]
    )
    return transcript


def test_retrieve_segments_uses_provider_and_limits_results(settings):
    from apps.coach.services import retrieve_segments

    settings.RETRIEVAL_PROVIDER = "stub"
    owner = _owner("coach-owner")
    item = _media_item(owner, "Focus")
    _transcript_with_segments(
        item,
        [
            "Lernen mit Fokus und Wiederholung",
            "Motivation durch kleine Schritte",
        ],
    )

    results = retrieve_segments("Wie lerne ich fokussierter?", owner=owner, limit=1)

    assert len(results) == 1
    result = results[0]
    assert result.media_item_id == item.id
    assert result.transcript_id is not None
    assert result.segment_id is not None
    assert result.start_seconds is not None
    assert result.score > 0


def test_retrieve_segments_filters_to_owner(settings):
    from apps.coach.services import retrieve_segments

    settings.RETRIEVAL_PROVIDER = "stub"
    owner = _owner("coach-visible-owner")
    other_owner = _owner("coach-hidden-owner")

    visible_item = _media_item(owner, "Visible")
    hidden_item = _media_item(other_owner, "Hidden")

    _transcript_with_segments(visible_item, ["Fokus und Lernsysteme"])
    _transcript_with_segments(hidden_item, ["Vertrauliche Inhalte eines anderen Nutzers"])

    results = retrieve_segments("Lernsysteme", owner=owner, limit=5)

    assert results
    assert {result.media_item_id for result in results} == {visible_item.id}


@pytest.mark.skipif(connection.vendor != "postgresql", reason="requires PostgreSQL FTS")
def test_postgres_fts_provider_returns_ranked_segments(settings):
    from apps.coach.services import retrieve_segments

    settings.RETRIEVAL_PROVIDER = "postgres_fts"
    owner = _owner("coach-postgres-owner")
    item = _media_item(owner, "Deep Work")
    _transcript_with_segments(
        item,
        [
            "Fokus Deep Work Lernsystem",
            "Ablenkung vermeiden fuer Fokus",
        ],
    )

    results = retrieve_segments("Deep Work Fokus", owner=owner, limit=2)

    assert len(results) == 2
    assert results[0].score >= results[1].score
    assert all(result.media_item_id == item.id for result in results)
