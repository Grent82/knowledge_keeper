from decimal import Decimal
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole
from apps.coach.ports import CoachAnswer, ScoredSegment
from apps.knowledge_notes.models import KnowledgeNote
from apps.knowledge_notes.similarity import cosine_similarity

pytestmark = pytest.mark.django_db


class _StubEmbeddingProvider:
    def __init__(self, vector: list[float]):
        self.vector = vector

    def embed_text(self, text: str) -> list[float]:
        return self.vector


def _owner(username: str) -> User:
    return User.objects.create_user(username=username, password="secret", role=UserRole.OWNER)


def test_cosine_similarity_identical_vectors():
    assert cosine_similarity([1.0, 2.0], [1.0, 2.0]) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


@patch("apps.knowledge_notes.views.get_embedding_provider")
def test_semantic_search_returns_notes_by_similarity(mock_get_embedding_provider):
    owner = _owner("semantic-search-owner")
    KnowledgeNote.objects.create(
        owner=owner,
        title="Closer note",
        content_markdown="First note",
        embedding=[1.0, 0.0],
    )
    KnowledgeNote.objects.create(
        owner=owner,
        title="Farther note",
        content_markdown="Second note",
        embedding=[0.0, 1.0],
    )

    client = APIClient()
    client.force_authenticate(user=owner)
    mock_get_embedding_provider.return_value = _StubEmbeddingProvider([1.0, 0.0])

    response = client.get("/api/knowledge-notes/", {"semantic": "true", "q": "test"})

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert [entry["title"] for entry in payload] == ["Closer note"]


def test_semantic_search_without_q_returns_all():
    owner = _owner("semantic-search-no-q-owner")
    first_note = KnowledgeNote.objects.create(owner=owner, title="First semantic")
    second_note = KnowledgeNote.objects.create(owner=owner, title="Second semantic")

    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.get("/api/knowledge-notes/", {"semantic": "true"})

    assert response.status_code == 200
    assert {entry["id"] for entry in response.json()} == {first_note.id, second_note.id}


@patch("apps.coach.views.get_embedding_provider")
@patch("apps.coach.views.get_chat_provider")
@patch("apps.coach.views.retrieve_segments")
def test_coach_response_includes_relevant_notes(
    mock_retrieve_segments,
    mock_get_chat_provider,
    mock_get_embedding_provider,
):
    owner = _owner("coach-semantic-owner")
    note = KnowledgeNote.objects.create(
        owner=owner,
        title="Semantic note",
        summary_sentence="Kurzfassung",
        embedding=[1.0, 0.0],
    )

    client = APIClient()
    client.force_authenticate(user=owner)

    mock_retrieve_segments.return_value = [
        ScoredSegment(
            segment_id=11,
            transcript_id=22,
            media_item_id=33,
            content="Fokus entsteht durch klare Wiederholung.",
            snippet="Fokus entsteht durch klare Wiederholung.",
            score=0.9,
            start_seconds=Decimal("12.500"),
        )
    ]
    mock_get_chat_provider.return_value.generate_answer.return_value = CoachAnswer(
        answer="Arbeite mit klaren Wiederholungsblaecken.",
        mode="grounded_answer",
    )
    mock_get_embedding_provider.return_value = _StubEmbeddingProvider([1.0, 0.0])

    response = client.post(
        "/api/coach/chat/",
        {"question": "Wie lerne ich fokussierter?"},
        format="json",
    )

    assert response.status_code == 200
    assert "relevant_notes" in response.data
    assert response.data["relevant_notes"] == [
        {
            "note_id": note.id,
            "title": "Semantic note",
            "summary": "Kurzfassung",
            "score": 1.0,
        }
    ]
