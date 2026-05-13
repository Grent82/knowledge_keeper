from apps.knowledge_notes.providers.openai_compatible import StubNoteProvider


def test_stub_note_provider_titles_do_not_leak_internal_marker():
    notes = StubNoteProvider().generate("Kurzer Transcriptinhalt")

    assert notes
    assert all("[Stub]" not in note.title for note in notes)
