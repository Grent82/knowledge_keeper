from apps.knowledge_notes.ports import NoteResult
from apps.knowledge_notes.providers.openai_compatible import (
    OpenAICompatibleNoteProvider,
    _build_summaries_section,
    _build_transcript_sections,
    _extract_json_array,
    _filter_note_results,
)


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


def test_build_summaries_section_includes_all_ready_kinds():
    section = _build_summaries_section({
        "short": "Klarheit entsteht durch Reduktion.",
        "bullet": "- Fokus\n- Reduktion",
        "detailed": "Eine ausfuehrliche Erklaerung.",
    })

    assert "Kurzzusammenfassung" in section
    assert "Bullet-Zusammenfassung" in section
    assert "Detailzusammenfassung" in section
    assert "Klarheit entsteht durch Reduktion." in section
    assert "NICHT als Quelle zitieren" in section


def test_build_summaries_section_returns_empty_string_for_empty_input():
    assert _build_summaries_section({}) == ""


def test_extract_json_array_recovers_array_from_wrapped_text():
    raw = (
        "Hier ist das Ergebnis:\\n```json\\n"
        "[{\"title\":\"Ich erkenne etwas\",\"kind\":\"insight\"}]\\n```"
    )

    items = _extract_json_array(raw)

    assert items == [{"title": "Ich erkenne etwas", "kind": "insight"}]


def test_note_provider_disables_qwen_thinking_mode():
    captured: dict[str, object] = {}

    class DummyCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)

            class Message:
                content = "[]"
                model_extra = {}

            class Choice:
                message = Message()
                model_extra = {}

            class Response:
                choices = [Choice()]

            return Response()

    class DummyChat:
        completions = DummyCompletions()

    provider = OpenAICompatibleNoteProvider("https://example.com", "test-key", "test-model")
    provider._client = type("DummyClient", (), {"chat": DummyChat()})()

    provider.generate("Kurzes Transkript.", language_code="de", summaries={"short": "Kurz"})

    assert captured["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}
