import pytest

from apps.accounts.models import UserRole
from apps.knowledge_notes.models import KnowledgeNote

pytestmark = pytest.mark.django_db


def test_q_filter_matches_title_and_content(client, django_user_model, db):
    owner = django_user_model.objects.create_user(
        username="owner-note-search",
        password="secret",
        role=UserRole.OWNER,
    )
    matching_title = KnowledgeNote.objects.create(
        owner=owner,
        title="Foo title match",
        content_markdown="Something else",
    )
    matching_content = KnowledgeNote.objects.create(
        owner=owner,
        title="Other note",
        content_markdown="Contains foo in the body",
    )
    KnowledgeNote.objects.create(
        owner=owner,
        title="Irrelevant",
        content_markdown="No matching text here",
    )
    client.force_login(owner)

    response = client.get("/api/knowledge-notes/", {"q": "foo"})

    assert response.status_code == 200
    assert {entry["id"] for entry in response.json()} == {matching_title.id, matching_content.id}


def test_empty_q_returns_all_notes(client, django_user_model, db):
    owner = django_user_model.objects.create_user(
        username="owner-note-search-empty",
        password="secret",
        role=UserRole.OWNER,
    )
    first_note = KnowledgeNote.objects.create(owner=owner, title="First")
    second_note = KnowledgeNote.objects.create(owner=owner, title="Second")
    client.force_login(owner)

    response = client.get("/api/knowledge-notes/", {"q": "   "})

    assert response.status_code == 200
    assert {entry["id"] for entry in response.json()} == {first_note.id, second_note.id}
