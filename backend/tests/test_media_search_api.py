import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole
from apps.media_library.models import Category, MediaItem, MediaType, Tag

pytestmark = pytest.mark.django_db


def test_search_returns_matching_categories_tags_and_media_items():
    owner = User.objects.create_user(
        username="owner-search",
        password="secret",
        role=UserRole.OWNER,
    )
    category = Category.objects.create(name="Good Relationships", created_by=owner)
    tag = Tag.objects.create(name="relationship", created_by=owner)
    item = MediaItem.objects.create(
        title="What Is a Good Relationship",
        description="Relationship guidance",
        media_type=MediaType.AUDIO,
        owner=owner,
    )
    item.categories.add(category)
    item.tags.add(tag)
    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.get("/api/media/search", {"q": "relationship"})

    assert response.status_code == 200
    assert response.data["categories"][0]["name"] == "Good Relationships"
    assert response.data["tags"][0]["name"] == "relationship"
    assert response.data["media_items"][0]["title"] == "What Is a Good Relationship"
