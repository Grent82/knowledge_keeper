from apps.knowledge_notes.ports import NoteResult
from apps.knowledge_notes.providers.openai_compatible import (
    StubNoteProvider,
    _build_transcript_sections,
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
    assert all(note.summary_sentence for note in notes)
    assert all(note.source_excerpt for note in notes)
    assert all(note.why_it_matters for note in notes)


def test_filter_note_results_drops_transcript_like_and_generic_notes():
    results = _filter_note_results(
        [
            NoteResult(
                title="Schwaecher Insight",
                kind="insight",
                content_markdown=" ".join(["rohtext"] * 80),
                summary_sentence="Rohtext",
                source_excerpt="Rohtext",
                why_it_matters="Zu lang und unbrauchbar.",
            ),
            NoteResult(
                title="Generische Reflexion",
                kind="reflection",
                content_markdown=(
                    "Welche Aussage aus dem Inhalt trifft dich am meisten "
                    "und was bedeutet sie fuer dein Denken?"
                ),
                summary_sentence="Eine generische Frage.",
                source_excerpt="Kurze Passage",
                why_it_matters="Sollte wegen generischer Form wegfallen.",
            ),
            NoteResult(
                title="Ich pruefe meinen Widerstand",
                kind="action",
                content_markdown=(
                    "Notiere heute eine Ueberzeugung, die dir im Alltag Widerstand erzeugt, "
                    "und pruefe einen Gegenentwurf."
                ),
                summary_sentence="Pruefe eine Ueberzeugung.",
                source_excerpt="Ueberzeugung im Alltag",
                why_it_matters="Macht die Idee praktisch pruefbar.",
                problem="Ich reagiere automatisch und bleibe im Widerstand haengen.",
                first_step="Notiere heute einen Widerstand und pruefe einen Gegenentwurf.",
            ),
        ]
    )

    assert len(results) == 1
    assert results[0].title == "Ich pruefe meinen Widerstand"


def test_build_transcript_sections_spreads_context_across_later_ideas():
    sections = _build_transcript_sections(
        (
            "Erster Gedanke: Leistung wird oft mit Anstrengung verwechselt. "
            "Viele Menschen verteidigen diesen Gedanken automatisch. "
            "Zweiter Gedanke: Beziehungen werden stabiler, wenn Erwartungen klar benannt werden. "
            "Missverstaendnisse entstehen oft aus unausgesprochenen Annahmen. "
            "Dritter Gedanke: Lernen wird leichter, wenn Wiederholung klein und "
            "regelmaessig bleibt. "
            "Ein kurzes Ritual ist oft wirksamer als ein grosser Vorsatz."
        )
    )

    combined = " ".join(section["focus_sentence"] for section in sections)

    assert len(sections) >= 3
    assert "Erster Gedanke" in combined
    assert "Zweiter Gedanke" in combined
    assert "Dritter Gedanke" in combined


def test_filter_note_results_deduplicates_near_duplicate_candidates():
    results = _filter_note_results(
        [
            NoteResult(
                title="Ich pruefe meinen Glaubenssatz",
                kind="action",
                content_markdown=(
                    "Notiere heute eine Ueberzeugung, die dir im Alltag Widerstand erzeugt, "
                    "und pruefe einen Gegenentwurf."
                ),
                summary_sentence="Pruefe eine Ueberzeugung.",
                source_excerpt="Ueberzeugung im Alltag",
                why_it_matters="Macht die Idee praktisch pruefbar.",
                problem="Ich halte an einer unprueften Ueberzeugung fest.",
                first_step="Notiere heute einen Glaubenssatz und pruefe einen Gegenentwurf.",
            ),
            NoteResult(
                title="Ich pruefe meinen Glaubenssatz",
                kind="action",
                content_markdown=(
                    "Notiere heute eine Ueberzeugung, die dir im Alltag Widerstand erzeugt, "
                    "und pruefe einen Gegenentwurf."
                ),
                summary_sentence="Pruefe eine Ueberzeugung.",
                source_excerpt="Ueberzeugung im Alltag",
                why_it_matters="Macht die Idee praktisch pruefbar.",
                problem="Ich halte an einer unprueften Ueberzeugung fest.",
                first_step="Notiere heute einen Glaubenssatz und pruefe einen Gegenentwurf.",
            ),
            NoteResult(
                title="Ich plane mein Lernritual",
                kind="action",
                content_markdown=(
                    "Plane fuer morgen ein kurzes Wiederholungsritual mit fester Uhrzeit ein."
                ),
                summary_sentence="Plane ein Lernritual.",
                source_excerpt="Kurzes Wiederholungsritual",
                why_it_matters="Verankert Lernen im Alltag.",
                problem="Ich lerne unregelmaessig und verliere dadurch Kontinuitaet.",
                first_step="Plane heute ein kurzes Lernritual mit fester Uhrzeit.",
            ),
        ]
    )

    assert len(results) == 2
    assert [note.title for note in results] == [
        "Ich pruefe meinen Glaubenssatz",
        "Ich plane mein Lernritual",
    ]
