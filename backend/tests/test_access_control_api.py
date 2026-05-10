import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole
from apps.media_library.models import Category, MediaItem, MediaType

pytestmark = pytest.mark.django_db


def test_owner_can_assign_category_visibility_to_restricted_user():
    owner = User.objects.create_user(
        username="owner-assign",
        password="secret",
        role=UserRole.OWNER,
    )
    restricted = User.objects.create_user(
        username="restricted-assign",
        password="secret",
        role=UserRole.RESTRICTED_USER,
    )
    category = Category.objects.create(name="Mindset", created_by=owner)
    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.post(
        "/api/access/category-assignments",
        {"user": restricted.id, "category": category.id},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["user"] == restricted.id


def test_restricted_user_only_sees_visible_media_items():
    owner = User.objects.create_user(
        username="owner-visible",
        password="secret",
        role=UserRole.OWNER,
    )
    restricted = User.objects.create_user(
        username="restricted-visible",
        password="secret",
        role=UserRole.RESTRICTED_USER,
    )
    visible_category = Category.objects.create(name="Focus", created_by=owner)
    hidden_category = Category.objects.create(name="Private", created_by=owner)
    visible_item = MediaItem.objects.create(
        title="Visible",
        media_type=MediaType.AUDIO,
        owner=owner,
    )
    hidden_item = MediaItem.objects.create(title="Hidden", media_type=MediaType.AUDIO, owner=owner)
    visible_item.categories.add(visible_category)
    hidden_item.categories.add(hidden_category)
    owner_client = APIClient()
    owner_client.force_authenticate(user=owner)
    owner_client.post(
        "/api/access/category-assignments",
        {"user": restricted.id, "category": visible_category.id},
        format="json",
    )

    restricted_client = APIClient()
    restricted_client.force_authenticate(user=restricted)

    response = restricted_client.get("/api/media/items")

    assert response.status_code == 200
    assert [item["title"] for item in response.data] == ["Visible"]
