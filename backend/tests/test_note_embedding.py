from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.test import override_settings

from apps.accounts.models import User, UserRole
from apps.knowledge_notes.models import KnowledgeNote
from apps.knowledge_notes.tasks import update_note_embedding

pytestmark = pytest.mark.django_db


@patch("apps.knowledge_notes.providers.get_embedding_provider")
def test_update_note_embedding_task_stores_embedding(mock_get_provider):
    mock_get_provider.return_value.embed_text.return_value = [0.1, 0.2, 0.3]
    owner = User.objects.create_user(
        username="owner-note-embedding",
        password="secret",
        role=UserRole.OWNER,
    )
    note = KnowledgeNote.objects.create(
        owner=owner,
        title="Embedding title",
        content_markdown="Some markdown content",
    )

    update_note_embedding(note.id)

    note.refresh_from_db()
    assert note.embedding == [0.1, 0.2, 0.3]
    assert note.embedding_updated_at is not None


def test_regenerate_command_runs_without_error():
    stdout = StringIO()

    call_command("regenerate_note_embeddings", stdout=stdout)

    assert "Queuing embeddings for 0 notes..." in stdout.getvalue()
    assert "Done." in stdout.getvalue()


@override_settings(
    AI_HUB_BASE_URL="https://example.invalid/v1",
    AI_HUB_API_KEY="secret",
    AI_HUB_MODEL="chat-model",
    AI_HUB_EMBEDDING_MODEL="embedding-model",
)
@patch("apps.knowledge_notes.providers.openai_embedding.OpenAICompatibleEmbeddingProvider")
def test_embedding_provider_uses_dedicated_embedding_model(mock_provider_class):
    from apps.knowledge_notes.providers import get_embedding_provider

    get_embedding_provider()

    mock_provider_class.assert_called_once_with(
        base_url="https://example.invalid/v1",
        api_key="secret",
        model="embedding-model",
    )


@patch("apps.knowledge_notes.providers.get_embedding_provider")
def test_update_note_embedding_task_degrades_safely_on_provider_error(mock_get_provider):
    mock_get_provider.return_value.embed_text.side_effect = RuntimeError("embedding unavailable")
    owner = User.objects.create_user(
        username="owner-note-embedding-failure",
        password="secret",
        role=UserRole.OWNER,
    )
    note = KnowledgeNote.objects.create(
        owner=owner,
        title="Embedding title",
        content_markdown="Some markdown content",
    )

    update_note_embedding(note.id)

    note.refresh_from_db()
    assert note.embedding is None
    assert note.embedding_updated_at is None
