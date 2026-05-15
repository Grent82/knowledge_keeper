from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command

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
