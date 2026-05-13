from apps.knowledge_notes.providers.openai_compatible import StubNoteProvider


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
