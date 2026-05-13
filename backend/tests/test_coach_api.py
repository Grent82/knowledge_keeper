from decimal import Decimal
from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole
from apps.coach.ports import ScoredSegment

pytestmark = pytest.mark.django_db


def _user(username: str, role: str = UserRole.OWNER) -> User:
    return User.objects.create_user(username=username, password="secret", role=role)


@patch("apps.coach.views.get_chat_provider")
@patch("apps.coach.views.retrieve_segments")
def test_chat_endpoint_returns_answer_and_citations(mock_retrieve_segments, mock_get_chat_provider):
    owner = _user("coach-api-owner")
    client = APIClient()
    client.force_authenticate(user=owner)

    mock_retrieve_segments.return_value = [
        ScoredSegment(
            segment_id=11,
            transcript_id=22,
            media_item_id=33,
            content="Fokus entsteht durch klare Wiederholung.",
            score=0.9,
            start_seconds=Decimal("12.500"),
        )
    ]
    mock_get_chat_provider.return_value.generate_answer.return_value = (
        "Arbeite mit klaren Wiederholungsblaecken."
    )

    response = client.post(
        "/api/coach/chat/",
        {
            "question": "Wie lerne ich fokussierter?",
            "history": [{"role": "user", "content": "Ich verliere schnell den Fokus."}],
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.data["answer"] == "Arbeite mit klaren Wiederholungsblaecken."
    assert response.data["cited_segments"][0]["segment_id"] == 11
    mock_retrieve_segments.assert_called_once_with(
        "Wie lerne ich fokussierter?", owner=owner, limit=5
    )
    mock_get_chat_provider.return_value.generate_answer.assert_called_once_with(
        question="Wie lerne ich fokussierter?",
        history=[{"role": "user", "content": "Ich verliere schnell den Fokus."}],
        segments=mock_retrieve_segments.return_value,
    )


def test_chat_endpoint_rejects_unauthenticated_requests():
    client = APIClient()

    response = client.post(
        "/api/coach/chat/",
        {"question": "Wie lerne ich fokussierter?"},
        format="json",
    )

    assert response.status_code in {401, 403}


def test_chat_endpoint_rejects_invalid_history_format():
    owner = _user("coach-api-invalid")
    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.post(
        "/api/coach/chat/",
        {
            "question": "Wie lerne ich fokussierter?",
            "history": [{"role": "system", "content": "invalid"}],
        },
        format="json",
    )

    assert response.status_code == 400
    assert "history" in response.data


@patch("apps.coach.views.get_chat_provider")
@patch("apps.coach.views.retrieve_segments")
def test_chat_endpoint_returns_empty_citations_when_no_hits(
    mock_retrieve_segments, mock_get_chat_provider
):
    owner = _user("coach-api-no-hits")
    client = APIClient()
    client.force_authenticate(user=owner)

    mock_retrieve_segments.return_value = []
    mock_get_chat_provider.return_value.generate_answer.return_value = (
        "Ich habe aktuell keine passenden Stellen in deiner Wissensbasis gefunden."
    )

    response = client.post(
        "/api/coach/chat/",
        {"question": "Was weiss ich ueber Stoizismus?"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["cited_segments"] == []
    assert "keine passenden" in response.data["answer"]
