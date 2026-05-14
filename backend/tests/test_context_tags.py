from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole
from apps.coach.ports import CoachAnswer
from apps.knowledge_notes.models import KnowledgeNote

pytestmark = pytest.mark.django_db


class _StubEmbeddingProvider:
    def __init__(self, vector: list[float]):
        self.vector = vector

    def embed_text(self, text: str) -> list[float]:
        return self.vector


def _owner(username: str) -> User:
    return User.objects.create_user(username=username, password="secret", role=UserRole.OWNER)


def test_context_tags_endpoint_returns_list():
    owner = _owner("context-tags-owner")
    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.get("/api/knowledge-notes/context-tags/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert "kontext:Konflikt" in response.json()


def test_tag_filter_returns_matching_notes():
    owner = _owner("tag-filter-owner")
    matching_note = KnowledgeNote.objects.create(
        owner=owner,
        title="Conflict note",
        context_tags=["kontext:Konflikt"],
    )
    KnowledgeNote.objects.create(
        owner=owner,
        title="Other note",
        context_tags=["kontext:Arbeit"],
    )
    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.get("/api/knowledge-notes/", {"tag": "kontext:Konflikt"})

    assert response.status_code == 200
    assert [entry["id"] for entry in response.json()] == [matching_note.id]


def test_tag_filter_returns_all_when_no_tag():
    owner = _owner("tag-filter-all-owner")
    first_note = KnowledgeNote.objects.create(owner=owner, title="First note")
    second_note = KnowledgeNote.objects.create(owner=owner, title="Second note")
    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.get("/api/knowledge-notes/")

    assert response.status_code == 200
    assert {entry["id"] for entry in response.json()} == {first_note.id, second_note.id}


@patch("apps.knowledge_notes.views.get_embedding_provider")
def test_tag_filter_applies_after_semantic_search(mock_get_embedding_provider):
    owner = _owner("tag-filter-semantic-owner")
    KnowledgeNote.objects.create(
        owner=owner,
        title="Semantic only note",
        context_tags=["kontext:Arbeit"],
        embedding=[1.0, 0.0],
    )
    KnowledgeNote.objects.create(
        owner=owner,
        title="Different tag note",
        context_tags=["kontext:Konflikt"],
        embedding=[0.0, 1.0],
    )
    client = APIClient()
    client.force_authenticate(user=owner)
    mock_get_embedding_provider.return_value = _StubEmbeddingProvider([1.0, 0.0])

    response = client.get(
        "/api/knowledge-notes/",
        {"semantic": "true", "q": "conflict", "tag": "kontext:Konflikt"},
    )

    assert response.status_code == 200
    assert response.json() == []


@patch("apps.coach.views.get_chat_provider")
@patch("apps.coach.views.retrieve_segments")
def test_coach_accepts_context_tag(mock_retrieve_segments, mock_get_chat_provider):
    owner = _owner("coach-context-tag-owner")
    client = APIClient()
    client.force_authenticate(user=owner)

    mock_retrieve_segments.return_value = []
    mock_get_chat_provider.return_value.generate_answer.return_value = CoachAnswer(
        answer="Arbeite mit einer ruhigen Naechstes-Schritt-Perspektive.",
        mode="grounded_answer",
    )

    response = client.post(
        "/api/coach/chat/",
        {"question": "Wie komme ich aus der Starre?", "context_tag": "kontext:Unsicherheit"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["context_tag"] == "kontext:Unsicherheit"
    mock_retrieve_segments.assert_called_once_with(
        "Wie komme ich aus der Starre? kontext:Unsicherheit", owner=owner, limit=5
    )
