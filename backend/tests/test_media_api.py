import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole
from apps.media_library.models import Category, MediaItem, MediaType, Tag

pytestmark = pytest.mark.django_db


def test_owner_can_create_media_item_from_asset_and_source():
    owner = User.objects.create_user(username="owner-media", password="secret", role=UserRole.OWNER)
    client = APIClient()
    client.force_authenticate(user=owner)

    asset_response = client.post(
        "/api/media/assets",
        {
            "origin": "local_upload",
            "file_format": "mp4",
            "mime_type": "video/mp4",
            "storage_path": "media/video.mp4",
        },
        format="json",
    )
    source_response = client.post(
        "/api/media/sources",
        {
            "provider": "youtube",
            "source_url": "https://youtube.com/watch?v=abc123",
            "external_id": "abc123",
            "title": "Clip",
        },
        format="json",
    )
    item_response = client.post(
        "/api/media/items",
        {
            "title": "Clip",
            "media_type": "video",
            "asset": asset_response.data["id"],
            "external_source": source_response.data["id"],
            "categories": [],
            "tags": [],
        },
        format="json",
    )

    assert asset_response.status_code == 201
    assert source_response.status_code == 201
    assert item_response.status_code == 201
    assert item_response.data["owner"] == owner.id


def test_owner_can_upload_media_asset_file():
    owner = User.objects.create_user(
        username="owner-upload",
        password="secret",
        role=UserRole.OWNER,
    )
    client = APIClient()
    client.force_authenticate(user=owner)
    uploaded_file = SimpleUploadedFile(
        "voice-note.mp3",
        b"fake-audio-data",
        content_type="audio/mpeg",
    )

    response = client.post(
        "/api/media/assets",
        {
            "origin": "local_upload",
            "file_format": "mp3",
            "uploaded_file": uploaded_file,
        },
        format="multipart",
    )

    assert response.status_code == 201
    assert response.data["filename"].startswith("voice-note")
    assert response.data["filename"].endswith(".mp3")
    assert response.data["asset_url"].endswith(response.data["filename"])


def test_restricted_user_cannot_create_media_item():
    restricted = User.objects.create_user(
        username="restricted-media",
        password="secret",
        role=UserRole.RESTRICTED_USER,
    )
    client = APIClient()
    client.force_authenticate(user=restricted)

    response = client.post(
        "/api/media/items",
        {"title": "Nope", "media_type": "audio", "categories": [], "tags": []},
        format="json",
    )

    assert response.status_code == 403


def test_owner_can_assign_categories_and_tags_to_media_item():
    owner = User.objects.create_user(
        username="owner-assign",
        password="secret",
        role=UserRole.OWNER,
    )
    category = Category.objects.create(name="Relationships", created_by=owner)
    tag = Tag.objects.create(name="communication", created_by=owner)
    media_item = MediaItem.objects.create(
        title="Better Conversations",
        media_type=MediaType.AUDIO,
        owner=owner,
    )
    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.patch(
        f"/api/media/items/{media_item.id}",
        {
          "categories": [category.id],
          "tags": [tag.id],
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.data["categories"] == [category.id]
    assert response.data["tags"] == [tag.id]
