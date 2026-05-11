import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole
from apps.knowledge_notes.models import KnowledgeNote
from apps.media_library.models import MediaItem, MediaType
from apps.playback.models import ArtifactStatus, Transcript

pytestmark = pytest.mark.django_db


def test_owner_can_crud_knowledge_note():
    owner = User.objects.create_user(
        username="owner-note-crud",
        password="secret",
        role=UserRole.OWNER,
    )
    client = APIClient()
    client.force_authenticate(user=owner)

    create_response = client.post(
        "/api/knowledge-notes/",
        {"title": "First note", "content_markdown": "# Hello", "linked_notes": []},
        format="json",
    )
    note_id = create_response.data["id"]
    list_response = client.get("/api/knowledge-notes/")
    update_response = client.patch(
        f"/api/knowledge-notes/{note_id}",
        {"title": "Updated note", "content_markdown": "Updated body"},
        format="json",
    )
    delete_response = client.delete(f"/api/knowledge-notes/{note_id}")

    assert create_response.status_code == 201
    assert create_response.data["owner"] == owner.id
    assert list_response.status_code == 200
    assert [entry["id"] for entry in list_response.data] == [note_id]
    assert update_response.status_code == 200
    assert update_response.data["title"] == "Updated note"
    assert delete_response.status_code == 204
    assert not KnowledgeNote.objects.filter(id=note_id).exists()


def test_non_owner_cannot_access_notes():
    restricted = User.objects.create_user(
        username="restricted-note",
        password="secret",
        role=UserRole.RESTRICTED_USER,
    )
    client = APIClient()
    client.force_authenticate(user=restricted)

    response = client.get("/api/knowledge-notes/")

    assert response.status_code == 403


def test_filter_by_media_item():
    owner = User.objects.create_user(
        username="owner-note-filter",
        password="secret",
        role=UserRole.OWNER,
    )
    first_item = MediaItem.objects.create(title="First", media_type=MediaType.AUDIO, owner=owner)
    second_item = MediaItem.objects.create(title="Second", media_type=MediaType.VIDEO, owner=owner)
    first_note = KnowledgeNote.objects.create(
        owner=owner,
        title="First note",
        media_item=first_item,
    )
    KnowledgeNote.objects.create(owner=owner, title="Second note", media_item=second_item)
    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.get(f"/api/knowledge-notes/?media_item={first_item.id}")

    assert response.status_code == 200
    assert [entry["id"] for entry in response.data] == [first_note.id]


def test_linked_notes_relation():
    owner = User.objects.create_user(
        username="owner-note-links",
        password="secret",
        role=UserRole.OWNER,
    )
    media_item = MediaItem.objects.create(title="Linked", media_type=MediaType.AUDIO, owner=owner)
    transcript = Transcript.objects.create(media_item=media_item, status=ArtifactStatus.READY)
    first_note = KnowledgeNote.objects.create(owner=owner, title="Alpha")
    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.post(
        "/api/knowledge-notes/",
        {
            "title": "Beta",
            "content_markdown": "Body",
            "media_item": media_item.id,
            "transcript": transcript.id,
            "linked_notes": [first_note.id],
        },
        format="json",
    )

    assert response.status_code == 201
    second_note = KnowledgeNote.objects.get(id=response.data["id"])
    assert list(second_note.linked_notes.values_list("id", flat=True)) == [first_note.id]
    assert response.data["linked_notes"] == [first_note.id]
