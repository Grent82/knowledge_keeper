from apps.knowledge_notes.ports import NoteResult
from apps.knowledge_notes.providers.openai_compatible import _filter_note_results


def _valid_note(**overrides):
    data = {
        "title": "Ich erkenne meinen naechsten Schritt",
        "kind": "insight",
        "content_markdown": "Ich halte kurz inne und pruefe, welche Annahme mich gerade blockiert.",
        "summary_sentence": "Eine blockierende Annahme wird sichtbar.",
        "source_excerpt": "Blockierende Annahme",
        "why_it_matters": "So bleibt die Erkenntnis spaeter erneut nutzbar.",
        "problem": "Ich reagiere automatisch und verliere dadurch Klarheit.",
        "core_insight": "Ich erkenne, dass meine Annahme mehr Druck als Wahrheit erzeugt.",
        "application": "Vor einem schwierigen Gespraech achte ich auf Enge in Brust und Schultern.",
        "first_step": "Schreibe heute eine blockierende Annahme konkret auf.",
        "deeper_principle": "Klarheit waechst, wenn ich Deutungen statt Fakten pruefe.",
        "context_tags": ["kontext:Konflikt"],
    }
    data.update(overrides)
    return NoteResult(**data)


def test_filter_rejects_note_without_ich_form_title():
    results = _filter_note_results([_valid_note(title="Der Inhalt zeigt eine Wahrheit")])

    assert results == []


def test_filter_rejects_note_with_empty_problem():
    results = _filter_note_results([_valid_note(problem="")])

    assert results == []


def test_filter_rejects_note_with_short_first_step():
    results = _filter_note_results([_valid_note(first_step="Mach das")])

    assert results == []


def test_filter_accepts_valid_transformation_note():
    results = _filter_note_results([_valid_note()])

    assert len(results) == 1
    assert results[0].title == "Ich erkenne meinen naechsten Schritt"
    assert results[0].problem == "Ich reagiere automatisch und verliere dadurch Klarheit."
    assert results[0].first_step == "Schreibe heute eine blockierende Annahme konkret auf."
    assert results[0].context_tags == ["kontext:Konflikt"]


def test_context_tags_list_is_validated():
    results = _filter_note_results([_valid_note(context_tags="kontext:Konflikt")])

    assert len(results) == 1
    assert results[0].context_tags == []
