from unittest.mock import patch

import pytest

from apps.accounts.models import User, UserRole
from apps.knowledge_notes.models import KnowledgeNote
from apps.knowledge_notes.ports import NoteResult
from apps.knowledge_notes.providers.stub_substance_gate import StubSubstanceGateProvider
from apps.media_library.models import MediaItem, MediaType
from apps.playback.models import ArtifactStatus, Transcript

pytestmark = pytest.mark.django_db


class _QualifiedNoteProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def generate(
        self,
        transcript_text: str,
        language_code: str = "",
        summaries: dict | None = None,
    ) -> list[NoteResult]:
        self.calls.append((transcript_text, language_code))
        return [
            NoteResult(
                title="Ich nutze klare Einsichten",
                kind="insight",
                content_markdown="Eine verdichtete Notiz.",
                summary_sentence="Eine klare Kernaussage.",
                source_excerpt="Kurzer Transkriptinhalt",
                why_it_matters="Sie macht die Kernidee schnell wiederverwendbar.",
                problem="Unklare Prioritaeten im Alltag.",
                core_insight="Ich erkenne, dass Klarheit vor Tempo kommt.",
                application="Bei der Tagesplanung vor dem ersten Meeting.",
                first_step="Schreibe heute drei Prioritaeten auf.",
                deeper_principle="Weniger Reibung schafft mehr Fokus.",
                context_tags=["kontext:planung", "kontext:fokus"],
            )
        ]


def _make_transcript(content: str) -> Transcript:
    owner = User.objects.create_user(
        username=f"owner-{User.objects.count()}",
        password="secret",
        role=UserRole.OWNER,
    )
    media_item = MediaItem.objects.create(
        title="Structured Notes",
        media_type=MediaType.AUDIO,
        owner=owner,
    )
    return Transcript.objects.create(
        media_item=media_item,
        status=ArtifactStatus.READY,
        content=content,
        language_code="de",
    )


def test_stub_gate_always_returns_7() -> None:
    assert StubSubstanceGateProvider().assess("anything") == 7


def test_stub_gate_passes_threshold() -> None:
    score = StubSubstanceGateProvider().assess("anything")

    assert score >= 6


@patch("apps.knowledge_notes.providers.openai_compatible.get_note_provider")
@patch("apps.knowledge_notes.tasks.get_substance_gate_provider")
def test_chunk_below_threshold_is_skipped(mock_get_gate, mock_get_provider) -> None:
    from apps.knowledge_notes.tasks import generate_knowledge_notes

    transcript = _make_transcript(" ".join(f"wort{i}" for i in range(100)))
    mock_get_gate.return_value.assess.return_value = 3

    generate_knowledge_notes.run(transcript.id)

    mock_get_provider.return_value.generate.assert_not_called()
    assert not KnowledgeNote.objects.filter(transcript=transcript).exists()


@patch("apps.knowledge_notes.providers.openai_compatible.get_note_provider")
@patch("apps.knowledge_notes.tasks.get_substance_gate_provider")
def test_chunk_above_threshold_is_processed(mock_get_gate, mock_get_provider) -> None:
    from apps.knowledge_notes.tasks import generate_knowledge_notes

    transcript = _make_transcript(" ".join(f"wort{i}" for i in range(100)))
    note_provider = _QualifiedNoteProvider()
    mock_get_gate.return_value.assess.return_value = 8
    mock_get_provider.return_value = note_provider

    generate_knowledge_notes.run(transcript.id)

    assert note_provider.calls == [(transcript.content, "de")]
    assert KnowledgeNote.objects.filter(transcript=transcript).count() == 1


def test_split_into_chunks_splits_correctly() -> None:
    from apps.knowledge_notes.tasks import _split_into_chunks

    text = " ".join(f"wort{i}" for i in range(1000))

    chunks = _split_into_chunks(text)

    assert len(chunks) == 2
    assert all(len(chunk.split()) == 500 for chunk in chunks)
