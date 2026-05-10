import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.media_library.models import (
    AssetOrigin,
    Category,
    ExternalSource,
    ExternalSourceProvider,
    MediaAsset,
    MediaFormat,
    MediaItem,
    MediaType,
    PlayerDisplayMode,
    Tag,
)

pytestmark = pytest.mark.django_db


def test_category_name_must_be_unique_per_parent():
    owner = User.objects.create_user(username="owner-a")
    parent = Category.objects.create(name="Human Elevation", created_by=owner)
    Category.objects.create(name="Masculinity", created_by=owner, parent=parent)

    duplicate_category = Category(name="Masculinity", created_by=owner, parent=parent)

    with pytest.raises(ValidationError):
        duplicate_category.full_clean(validate_constraints=True)


def test_category_name_can_repeat_under_different_parent():
    owner = User.objects.create_user(username="owner-d")
    first_parent = Category.objects.create(name="Mindset", created_by=owner)
    second_parent = Category.objects.create(name="Performance", created_by=owner)
    Category.objects.create(name="Focus", created_by=owner, parent=first_parent)

    category = Category(name="Focus", created_by=owner, parent=second_parent)
    category.full_clean(validate_constraints=True)


def test_media_item_can_link_asset_and_external_source():
    owner = User.objects.create_user(username="owner-b")
    tag = Tag.objects.create(name="podcast", created_by=owner)
    category = Category.objects.create(name="Mindset", created_by=owner)
    source = ExternalSource.objects.create(
        provider=ExternalSourceProvider.YOUTUBE,
        source_url="https://youtube.com/watch?v=abc123",
        external_id="abc123",
        title="Focus Session",
    )
    asset = MediaAsset.objects.create(
        origin=AssetOrigin.LOCAL_UPLOAD,
        file_format=MediaFormat.MP4,
        storage_path="media/focus-session.mp4",
        mime_type="video/mp4",
        duration_seconds=3600,
        width=1920,
        height=1080,
    )

    item = MediaItem.objects.create(
        title="Focus Session",
        media_type=MediaType.VIDEO,
        player_display_mode=PlayerDisplayMode.UNIFORM,
        owner=owner,
        asset=asset,
        external_source=source,
    )
    item.categories.add(category)
    item.tags.add(tag)

    assert item.asset == asset
    assert item.external_source == source
    assert list(item.categories.all()) == [category]
    assert list(item.tags.all()) == [tag]


def test_media_item_defaults_to_uniform_player_display():
    owner = User.objects.create_user(username="owner-c")

    item = MediaItem.objects.create(
        title="Audio Memo",
        media_type=MediaType.AUDIO,
        owner=owner,
    )

    assert item.player_display_mode == PlayerDisplayMode.UNIFORM
