from unittest.mock import patch

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole
from apps.knowledge_notes.models import KnowledgeNote
from apps.knowledge_notes.tasks import link_notes_by_principle

pytestmark = pytest.mark.django_db


class _ThresholdEmbeddingProvider:
    def embed_text(self, text: str) -> list[float]:
        if text == "same principle":
            return [1.0, 0.0]
        return [0.0, 1.0]


def _owner(username: str) -> User:
    return User.objects.create_user(username=username, password="secret", role=UserRole.OWNER)


@patch("apps.knowledge_notes.providers.get_embedding_provider")
def test_link_notes_by_principle_links_similar_notes(mock_get_embedding_provider):
    mock_get_embedding_provider.return_value = _ThresholdEmbeddingProvider()
    owner = _owner("principle-link-owner")
    first_note = KnowledgeNote.objects.create(
        owner=owner,
        title="First",
        deeper_principle="same principle",
    )
    second_note = KnowledgeNote.objects.create(
        owner=owner,
        title="Second",
        deeper_principle="same principle",
    )

    link_notes_by_principle(first_note.id)

    first_note.refresh_from_db()
    assert list(first_note.linked_notes.values_list("id", flat=True)) == [second_note.id]


def test_link_notes_skips_empty_principle():
    owner = _owner("empty-principle-owner")
    note = KnowledgeNote.objects.create(owner=owner, title="Empty", deeper_principle="")
    candidate = KnowledgeNote.objects.create(
        owner=owner,
        title="Candidate",
        deeper_principle="same principle",
    )

    link_notes_by_principle(note.id)

    note.refresh_from_db()
    assert list(note.linked_notes.values_list("id", flat=True)) == []
    assert list(candidate.linked_notes.values_list("id", flat=True)) == []


@patch("apps.knowledge_notes.views.get_embedding_provider")
def test_related_endpoint_returns_scored_list(mock_get_embedding_provider):
    mock_get_embedding_provider.return_value = _ThresholdEmbeddingProvider()
    owner = _owner("related-endpoint-owner")
    note = KnowledgeNote.objects.create(
        owner=owner,
        title="Anchor",
        deeper_principle="same principle",
    )
    related = KnowledgeNote.objects.create(
        owner=owner,
        title="Related",
        core_insight="A shared insight worth revisiting.",
        deeper_principle="same principle",
    )

    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.get(f"/api/knowledge-notes/{note.id}/related/")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": related.id,
            "title": "Related",
            "core_insight": "A shared insight worth revisiting.",
            "similarity_score": 1.0,
        }
    ]


def test_related_endpoint_returns_empty_for_no_principle():
    owner = _owner("related-empty-owner")
    note = KnowledgeNote.objects.create(owner=owner, title="No principle", deeper_principle="")

    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.get(f"/api/knowledge-notes/{note.id}/related/")

    assert response.status_code == 200
    assert response.json() == []


@override_settings(PRINCIPLE_LINK_THRESHOLD=0.99)
@patch("apps.knowledge_notes.providers.get_embedding_provider")
def test_principle_link_threshold_from_settings(mock_get_embedding_provider):
    owner = _owner("threshold-owner")
    first_note = KnowledgeNote.objects.create(
        owner=owner,
        title="First",
        deeper_principle="same principle",
    )
    perfect_match = KnowledgeNote.objects.create(
        owner=owner,
        title="Perfect",
        deeper_principle="same principle",
    )
    KnowledgeNote.objects.create(
        owner=owner,
        title="Imperfect",
        deeper_principle="different principle",
    )
    mock_get_embedding_provider.return_value = _ThresholdEmbeddingProvider()

    link_notes_by_principle(first_note.id)

    first_note.refresh_from_db()
    assert list(first_note.linked_notes.values_list("id", flat=True)) == [perfect_match.id]
