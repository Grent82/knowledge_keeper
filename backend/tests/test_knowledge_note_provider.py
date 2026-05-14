from apps.knowledge_notes.ports import NoteResult
from apps.knowledge_notes.providers.openai_compatible import (
    StubNoteProvider,
    _filter_note_results,
)


def test_stub_note_provider_titles_do_not_leak_internal_marker():
    notes = StubNoteProvider().generate("Kurzer Transcriptinhalt")

    assert notes
    assert all("[Stub]" not in note.title for note in notes)


def test_stub_note_provider_does_not_emit_developer_instructions_or_placeholder_copy():
    notes = StubNoteProvider().generate(
        "Wiederholung hilft beim Lernen. Kleine Schritte geben Orientierung."
    )

    contents = [note.content_markdown for note in notes]
    combined = "\n".join(contents)

    assert "KNOWLEDGE_NOTE_PROVIDER" not in combined
    assert "Django-Settings" not in combined
    assert "Platzhalter-Notiz" not in combined
    assert any("Wiederholung" in content or "Kleine Schritte" in content for content in contents)


def test_stub_note_provider_returns_concise_distilled_artifacts():
    notes = StubNoteProvider().generate(
        (
            "Wir glauben oft, dass wir uns anstrengen muessen, um voranzukommen. "
            "Starre Ueberzeugungen machen das Leben enger und anstrengender. "
            "Wer sie lockert, gewinnt mehr Handlungsspielraum."
        )
    )

    assert len(notes) == 3
    assert all(len(note.content_markdown.split()) <= 40 for note in notes)
    assert all("Welche Aussage aus dem Inhalt" not in note.content_markdown for note in notes)
    assert all("zum Beispiel:" not in note.content_markdown for note in notes)


def test_filter_note_results_drops_transcript_like_and_generic_notes():
    results = _filter_note_results(
        [
            NoteResult(
                title="Schwaecher Insight",
                kind="insight",
                content_markdown=" ".join(["rohtext"] * 80),
            ),
            NoteResult(
                title="Generische Reflexion",
                kind="reflection",
                content_markdown=(
                    "Welche Aussage aus dem Inhalt trifft dich am meisten "
                    "und was bedeutet sie fuer dein Denken?"
                ),
            ),
            NoteResult(
                title="Brauchbare Handlung",
                kind="action",
                content_markdown=(
                    "Notiere heute eine Ueberzeugung, die dir im Alltag Widerstand erzeugt, "
                    "und pruefe einen Gegenentwurf."
                ),
            ),
        ]
    )

    assert len(results) == 1
    assert results[0].title == "Brauchbare Handlung"
