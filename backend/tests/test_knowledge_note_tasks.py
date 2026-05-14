from unittest.mock import patch

import pytest

from apps.accounts.models import User, UserRole
from apps.knowledge_notes.models import KnowledgeNote
from apps.knowledge_notes.ports import NoteResult
from apps.media_library.models import MediaItem, MediaType
from apps.playback.models import ArtifactStatus, Transcript

pytestmark = pytest.mark.django_db


@patch("apps.knowledge_notes.providers.openai_compatible.get_note_provider")
def test_generate_knowledge_notes_persists_structured_fields(mock_get_provider):
    from apps.knowledge_notes.tasks import generate_knowledge_notes

    owner = User.objects.create_user(
        username="owner-note-task",
        password="secret",
        role=UserRole.OWNER,
    )
    media_item = MediaItem.objects.create(
        title="Structured Notes",
        media_type=MediaType.AUDIO,
        owner=owner,
    )
    transcript = Transcript.objects.create(
        media_item=media_item,
        status=ArtifactStatus.READY,
        content="Kurzer Transkriptinhalt mit einer klaren Idee.",
        language_code="de",
    )
    mock_get_provider.return_value.generate.return_value = [
        NoteResult(
            title="Klare Einsicht",
            kind="insight",
            content_markdown="Eine verdichtete Notiz.",
            summary_sentence="Eine klare Kernaussage.",
            source_excerpt="Kurzer Transkriptinhalt",
            why_it_matters="Sie macht die Kernidee schnell wiederverwendbar.",
        )
    ]

    generate_knowledge_notes.run(transcript.id)

    note = KnowledgeNote.objects.get(transcript=transcript)
    assert note.title == "Klare Einsicht"
    assert note.summary_sentence == "Eine klare Kernaussage."
    assert note.source_excerpt == "Kurzer Transkriptinhalt"
    assert note.why_it_matters == "Sie macht die Kernidee schnell wiederverwendbar."
