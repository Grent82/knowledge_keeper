from unittest.mock import patch

import pytest

from apps.accounts.models import User, UserRole
from apps.media_library.models import MediaItem, MediaType, Tag
from apps.media_library.tasks import auto_tag_media_item
from apps.playback.models import ArtifactStatus, Summary, SummaryKind, Transcript

pytestmark = pytest.mark.django_db


def _owner(username: str) -> User:
    return User.objects.create_user(username=username, role=UserRole.OWNER)


def _media_item(owner: User, title: str = "Test Item") -> MediaItem:
    from apps.media_library.models import MediaAsset

    asset = MediaAsset.objects.create(storage_path="test.mp3", created_by=owner)
    return MediaItem.objects.create(
        title=title, media_type=MediaType.AUDIO, owner=owner, asset=asset
    )


def _ready_transcript(media_item: MediaItem, content: str = "Transcript text") -> Transcript:
    return Transcript.objects.create(
        media_item=media_item,
        status=ArtifactStatus.READY,
        content=content,
        language_code="de",
    )


def _ready_short_summary(media_item: MediaItem, transcript: Transcript, content: str) -> Summary:
    return Summary.objects.create(
        media_item=media_item,
        transcript=transcript,
        kind=SummaryKind.SHORT,
        status=ArtifactStatus.READY,
        content=content,
    )


@patch("apps.media_library.tasks.get_tagging_provider")
def test_auto_tag_uses_short_summary_as_source(mock_get_provider):
    """Tags are derived from the short summary content when available."""
    mock_provider = mock_get_provider.return_value
    mock_provider.suggest_tags.return_value = ["lernen", "methodik"]

    owner = _owner("tag-user-summary")
    item = _media_item(owner)
    transcript = _ready_transcript(item, content="This is transcript content")
    _ready_short_summary(item, transcript, content="This is the short summary")

    auto_tag_media_item(item.id)

    mock_provider.suggest_tags.assert_called_once_with("This is the short summary")
    tag_names = list(item.tags.values_list("name", flat=True))
    assert "lernen" in tag_names
    assert "methodik" in tag_names


@patch("apps.media_library.tasks.get_tagging_provider")
def test_auto_tag_falls_back_to_transcript_when_no_short_summary(mock_get_provider):
    """Tags are derived from transcript content when no short summary is available."""
    mock_provider = mock_get_provider.return_value
    mock_provider.suggest_tags.return_value = ["gedächtnis"]

    owner = _owner("tag-user-fallback")
    item = _media_item(owner)
    _ready_transcript(item, content="Transcript fallback text")

    auto_tag_media_item(item.id)

    mock_provider.suggest_tags.assert_called_once_with("Transcript fallback text")
    assert item.tags.filter(name="gedächtnis").exists()


@patch("apps.media_library.tasks.get_tagging_provider")
def test_auto_tag_reuses_existing_global_tag(mock_get_provider):
    """An existing Tag with a matching name (case-insensitive) is reused, not duplicated."""
    mock_provider = mock_get_provider.return_value
    mock_provider.suggest_tags.return_value = ["Lernen"]  # proposed with capital L

    other_owner = _owner("tag-other-owner")
    existing_tag = Tag.objects.create(name="lernen", created_by=other_owner)

    owner = _owner("tag-user-reuse")
    item = _media_item(owner)
    _ready_transcript(item, content="content")
    _ready_short_summary(item, _ready_transcript(item), content="some summary")

    # Use the transcript-only path to keep setup simple
    item2 = _media_item(owner, title="Item 2")
    _ready_transcript(item2, content="some text")
    Summary.objects.create(
        media_item=item2,
        transcript=Transcript.objects.filter(media_item=item2).first(),
        kind=SummaryKind.SHORT,
        status=ArtifactStatus.READY,
        content="summary text",
    )

    auto_tag_media_item(item2.id)

    # No duplicate Tag records created
    assert Tag.objects.filter(name__iexact="lernen").count() == 1
    # The existing tag was reused
    assert item2.tags.filter(id=existing_tag.id).exists()


@patch("apps.media_library.tasks.get_tagging_provider")
def test_auto_tag_is_idempotent(mock_get_provider):
    """Running auto_tag_media_item twice does not produce duplicate tags."""
    mock_provider = mock_get_provider.return_value
    mock_provider.suggest_tags.return_value = ["kommunikation", "führung"]

    owner = _owner("tag-user-idempotent")
    item = _media_item(owner)
    _ready_transcript(item, content="content")
    _ready_short_summary(
        item, Transcript.objects.filter(media_item=item).first(), content="summary"
    )

    auto_tag_media_item(item.id)
    auto_tag_media_item(item.id)

    assert item.tags.filter(name="kommunikation").count() == 1
    assert item.tags.filter(name="führung").count() == 1
    assert Tag.objects.filter(name="kommunikation").count() == 1
    assert Tag.objects.filter(name="führung").count() == 1


@patch("apps.media_library.tasks.get_tagging_provider")
def test_auto_tag_preserves_manual_tags(mock_get_provider):
    """Existing manually assigned tags are not removed by auto-tagging."""
    mock_provider = mock_get_provider.return_value
    mock_provider.suggest_tags.return_value = ["strategie"]

    owner = _owner("tag-user-manual")
    item = _media_item(owner)
    manual_tag = Tag.objects.create(name="manuell", created_by=owner)
    item.tags.add(manual_tag)

    _ready_transcript(item, content="content")
    _ready_short_summary(
        item, Transcript.objects.filter(media_item=item).first(), content="summary"
    )

    auto_tag_media_item(item.id)

    # Manual tag still present
    assert item.tags.filter(name="manuell").exists()
    # AI tag also applied
    assert item.tags.filter(name="strategie").exists()
