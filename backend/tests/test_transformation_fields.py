from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole
from apps.knowledge_notes.models import KnowledgeNote

pytestmark = pytest.mark.django_db


def test_new_fields_are_optional():
    owner = User.objects.create_user(
        username="owner-note-transform-optional",
        password="secret",
        role=UserRole.OWNER,
    )
    note = KnowledgeNote.objects.create(
        owner=owner,
        title="Optional fields note",
        content_markdown="Body",
    )
    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.get(f"/api/knowledge-notes/{note.id}")

    assert response.status_code == 200
    assert response.data["problem"] == ""
    assert response.data["core_insight"] == ""
    assert response.data["application"] == ""
    assert response.data["first_step"] == ""
    assert response.data["deeper_principle"] == ""
    assert response.data["context_tags"] == []


@patch("apps.knowledge_notes.views.update_note_embedding.delay")
def test_new_fields_save_and_retrieve(mock_embedding_delay):
    owner = User.objects.create_user(
        username="owner-note-transform-save",
        password="secret",
        role=UserRole.OWNER,
    )
    client = APIClient()
    client.force_authenticate(user=owner)
    payload = {
        "title": "Transformation note",
        "content_markdown": "Body",
        "problem": "Ich verliere Fokus im Alltag.",
        "core_insight": "Ich erkenne, dass Klarheit Energie spart.",
        "application": "Bei der Wochenplanung am Montagmorgen.",
        "first_step": "Ich blocke heute 15 Minuten fuer Prioritaeten.",
        "deeper_principle": "Klare Entscheidungen reduzieren inneren Widerstand.",
        "context_tags": ["kontext:planung", "kontext:arbeit"],
        "linked_notes": [],
    }

    create_response = client.post("/api/knowledge-notes/", payload, format="json")

    assert create_response.status_code == 201
    note_id = create_response.data["id"]

    retrieve_response = client.get(f"/api/knowledge-notes/{note_id}")

    assert retrieve_response.status_code == 200
    assert retrieve_response.data["problem"] == payload["problem"]
    assert retrieve_response.data["core_insight"] == payload["core_insight"]
    assert retrieve_response.data["application"] == payload["application"]
    assert retrieve_response.data["first_step"] == payload["first_step"]
    assert retrieve_response.data["deeper_principle"] == payload["deeper_principle"]
    assert retrieve_response.data["context_tags"] == payload["context_tags"]


def test_context_tags_default_to_empty_list():
    owner = User.objects.create_user(
        username="owner-note-transform-tags",
        password="secret",
        role=UserRole.OWNER,
    )
    note = KnowledgeNote.objects.create(owner=owner, title="Default tags")

    assert note.context_tags == []
    assert KnowledgeNote.objects.get(id=note.id).context_tags == []
