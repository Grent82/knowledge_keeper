import math
from io import StringIO

import pytest
from django.core.management import call_command

from apps.accounts.models import User, UserRole
from apps.knowledge_notes.models import KnowledgeNote
from apps.knowledge_notes.providers.stub_embedding import StubEmbeddingProvider
from apps.knowledge_notes.tasks import update_note_embedding

pytestmark = pytest.mark.django_db


def test_stub_embedding_is_deterministic():
    provider = StubEmbeddingProvider()

    first = provider.embed_text("same text")
    second = provider.embed_text("same text")

    assert first == second


def test_stub_embedding_is_normalized():
    provider = StubEmbeddingProvider()

    vector = provider.embed_text("normalize me")

    assert math.isclose(sum(value**2 for value in vector), 1.0, rel_tol=1e-9)


def test_stub_embedding_different_texts_differ():
    provider = StubEmbeddingProvider()

    assert provider.embed_text("first text") != provider.embed_text("second text")


def test_update_note_embedding_task_stores_embedding():
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
    assert isinstance(note.embedding, list)
    assert len(note.embedding) == StubEmbeddingProvider.DIM
    assert all(isinstance(value, float) for value in note.embedding)
    assert note.embedding_updated_at is not None


def test_regenerate_command_runs_without_error():
    stdout = StringIO()

    call_command("regenerate_note_embeddings", stdout=stdout)

    assert "Queuing embeddings for 0 notes..." in stdout.getvalue()
    assert "Done." in stdout.getvalue()
