from unittest.mock import patch

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from apps.accounts.models import User, UserRole
from apps.knowledge_notes.models import KnowledgeNote, KnowledgeNoteLinkCandidate
from apps.knowledge_notes.tasks import link_notes_by_principle
from apps.knowledge_notes.tfidf import score_text_against_corpus

pytestmark = pytest.mark.django_db


class _ThresholdEmbeddingProvider:
    def embed_text(self, text: str) -> list[float]:
        if text == "same principle":
            return [1.0, 0.0]
        return [0.0, 1.0]


class _HybridEmbeddingProvider:
    def embed_text(self, text: str) -> list[float]:
        if text == "anchor principle":
            return [1.0, 0.0]
        if text in {"strong principle", "weak principle"}:
            return [0.8, 0.6]
        return [0.0, 1.0]


def _owner(username: str) -> User:
    return User.objects.create_user(username=username, password="secret", role=UserRole.OWNER)


@patch("apps.knowledge_notes.providers.get_embedding_provider")
def test_link_notes_by_principle_links_similar_notes(mock_get_embedding_provider):
    mock_get_embedding_provider.return_value = _ThresholdEmbeddingProvider()
    owner = _owner("principle-link-owner")
    first_note = KnowledgeNote.objects.create(
        owner=owner,
        title="First",
        deeper_principle="same principle",
    )
    second_note = KnowledgeNote.objects.create(
        owner=owner,
        title="Second",
        deeper_principle="same principle",
    )

    link_notes_by_principle(first_note.id)

    first_note.refresh_from_db()
    candidates = list(
        KnowledgeNoteLinkCandidate.objects.filter(source_note=first_note).values(
            "target_note_id",
            "embedding_score",
            "provenance",
        )
    )

    assert candidates == [
        {
            "target_note_id": second_note.id,
            "embedding_score": 1.0,
            "provenance": "embedding.deeper_principle",
        }
    ]
    assert list(first_note.linked_notes.values_list("id", flat=True)) == [second_note.id]


def test_link_notes_skips_empty_principle():
    owner = _owner("empty-principle-owner")
    note = KnowledgeNote.objects.create(owner=owner, title="Empty", deeper_principle="")
    candidate = KnowledgeNote.objects.create(
        owner=owner,
        title="Candidate",
        deeper_principle="same principle",
    )

    link_notes_by_principle(note.id)

    note.refresh_from_db()
    assert KnowledgeNoteLinkCandidate.objects.count() == 0
    assert list(note.linked_notes.values_list("id", flat=True)) == []
    assert list(candidate.linked_notes.values_list("id", flat=True)) == []


@patch("apps.knowledge_notes.providers.get_embedding_provider")
def test_link_notes_updates_existing_candidate_without_duplicates(mock_get_embedding_provider):
    mock_get_embedding_provider.return_value = _ThresholdEmbeddingProvider()
    owner = _owner("candidate-dedupe-owner")
    first_note = KnowledgeNote.objects.create(
        owner=owner,
        title="First",
        deeper_principle="same principle",
    )
    second_note = KnowledgeNote.objects.create(
        owner=owner,
        title="Second",
        deeper_principle="same principle",
    )

    link_notes_by_principle(first_note.id)
    link_notes_by_principle(first_note.id)

    assert (
        KnowledgeNoteLinkCandidate.objects.filter(
            source_note=first_note,
            target_note=second_note,
            provenance="embedding.deeper_principle",
        ).count()
        == 1
    )


@patch("apps.knowledge_notes.providers.get_embedding_provider")
def test_link_notes_keeps_candidates_owner_scoped(mock_get_embedding_provider):
    mock_get_embedding_provider.return_value = _ThresholdEmbeddingProvider()
    owner = _owner("candidate-owner-scope")
    other_owner = _owner("candidate-other-owner-scope")
    first_note = KnowledgeNote.objects.create(
        owner=owner,
        title="First",
        deeper_principle="same principle",
    )
    same_owner_match = KnowledgeNote.objects.create(
        owner=owner,
        title="Second",
        deeper_principle="same principle",
    )
    KnowledgeNote.objects.create(
        owner=other_owner,
        title="Third",
        deeper_principle="same principle",
    )

    link_notes_by_principle(first_note.id)

    assert list(
        KnowledgeNoteLinkCandidate.objects.filter(source_note=first_note).values_list(
            "target_note_id",
            flat=True,
        )
    ) == [same_owner_match.id]


def test_tfidf_scores_related_text_higher_than_unrelated_text():
    corpus = [
        "starre ueberzeugungen kosten energie und erzeugen widerstand",
        "innere programme und selbstwert beeinflussen handlungsspielraum",
        "morgenmeditation verbessert konzentration und ruhe",
    ]

    related_score = score_text_against_corpus(
        "starre ueberzeugungen und widerstand",
        "selbstwert und starre innere programme",
        corpus,
    )
    unrelated_score = score_text_against_corpus(
        "starre ueberzeugungen und widerstand",
        "morgenmeditation und ruhe",
        corpus,
    )

    assert related_score > unrelated_score
    assert related_score > 0.0


@patch("apps.knowledge_notes.providers.get_embedding_provider")
def test_link_notes_persists_tfidf_score_for_candidates(mock_get_embedding_provider):
    mock_get_embedding_provider.return_value = _ThresholdEmbeddingProvider()
    owner = _owner("candidate-tfidf-owner")
    first_note = KnowledgeNote.objects.create(
        owner=owner,
        title="Starre Ueberzeugungen",
        summary_sentence="Starre Ueberzeugungen erzeugen Widerstand.",
        deeper_principle="same principle",
    )
    second_note = KnowledgeNote.objects.create(
        owner=owner,
        title="Innere Programme",
        core_insight="Innere Programme und Ueberzeugungen formen Selbstwert.",
        deeper_principle="same principle",
    )

    link_notes_by_principle(first_note.id)

    candidate = KnowledgeNoteLinkCandidate.objects.get(
        source_note=first_note,
        target_note=second_note,
        provenance="embedding.deeper_principle",
    )

    assert candidate.tfidf_score > 0.0


@patch("apps.knowledge_notes.views.get_embedding_provider")
def test_related_endpoint_returns_scored_list(mock_get_embedding_provider):
    mock_get_embedding_provider.return_value = _ThresholdEmbeddingProvider()
    owner = _owner("related-endpoint-owner")
    note = KnowledgeNote.objects.create(
        owner=owner,
        title="Anchor",
        deeper_principle="same principle",
    )
    related = KnowledgeNote.objects.create(
        owner=owner,
        title="Related",
        core_insight="A shared insight worth revisiting.",
        deeper_principle="same principle",
    )

    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.get(f"/api/knowledge-notes/{note.id}/related/")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": related.id,
            "title": "Related",
            "core_insight": "A shared insight worth revisiting.",
            "similarity_score": 1.0,
        }
    ]


def test_related_endpoint_returns_empty_for_no_principle():
    owner = _owner("related-empty-owner")
    note = KnowledgeNote.objects.create(owner=owner, title="No principle", deeper_principle="")

    client = APIClient()
    client.force_authenticate(user=owner)

    response = client.get(f"/api/knowledge-notes/{note.id}/related/")

    assert response.status_code == 200
    assert response.json() == []


@override_settings(PRINCIPLE_LINK_THRESHOLD=0.99)
@patch("apps.knowledge_notes.providers.get_embedding_provider")
def test_principle_link_threshold_from_settings(mock_get_embedding_provider):
    owner = _owner("threshold-owner")
    first_note = KnowledgeNote.objects.create(
        owner=owner,
        title="First",
        deeper_principle="same principle",
    )
    perfect_match = KnowledgeNote.objects.create(
        owner=owner,
        title="Perfect",
        deeper_principle="same principle",
    )
    KnowledgeNote.objects.create(
        owner=owner,
        title="Imperfect",
        deeper_principle="different principle",
    )
    mock_get_embedding_provider.return_value = _ThresholdEmbeddingProvider()

    link_notes_by_principle(first_note.id)

    first_note.refresh_from_db()
    assert list(first_note.linked_notes.values_list("id", flat=True)) == [perfect_match.id]


@override_settings(PRINCIPLE_LINK_THRESHOLD=0.75, PRINCIPLE_LINK_FINAL_THRESHOLD=0.62)
@patch("apps.knowledge_notes.providers.get_embedding_provider")
def test_final_links_use_combined_candidate_score(mock_get_embedding_provider):
    mock_get_embedding_provider.return_value = _HybridEmbeddingProvider()
    owner = _owner("hybrid-ranking-owner")
    anchor = KnowledgeNote.objects.create(
        owner=owner,
        title="Anchor",
        summary_sentence="Starre Ueberzeugungen erzeugen Widerstand und kosten Energie.",
        deeper_principle="anchor principle",
    )
    strong_match = KnowledgeNote.objects.create(
        owner=owner,
        title="Strong",
        core_insight="Starre Ueberzeugungen und Widerstand binden Energie im Alltag.",
        deeper_principle="strong principle",
    )
    weak_match = KnowledgeNote.objects.create(
        owner=owner,
        title="Weak",
        core_insight="Morgenmeditation bringt Ruhe und Fokus.",
        deeper_principle="weak principle",
    )

    link_notes_by_principle(anchor.id)

    anchor.refresh_from_db()
    candidates = {
        candidate.target_note_id: candidate
        for candidate in KnowledgeNoteLinkCandidate.objects.filter(source_note=anchor)
    }

    assert candidates[strong_match.id].embedding_score == candidates[weak_match.id].embedding_score
    assert candidates[strong_match.id].tfidf_score > candidates[weak_match.id].tfidf_score
    assert candidates[strong_match.id].combined_score > candidates[weak_match.id].combined_score
    assert list(anchor.linked_notes.values_list("id", flat=True)) == [strong_match.id]


@override_settings(
    PRINCIPLE_LINK_THRESHOLD=0.75,
    PRINCIPLE_LINK_FINAL_THRESHOLD=0.62,
    PRINCIPLE_LINK_RERANK_ENABLED=True,
    PRINCIPLE_LINK_RERANK_TOP_K=1,
)
@patch("apps.knowledge_notes.tasks.get_link_reranker_provider")
@patch("apps.knowledge_notes.providers.get_embedding_provider")
def test_reranker_only_sees_top_k_candidates(
    mock_get_embedding_provider,
    mock_get_reranker_provider,
):
    mock_get_embedding_provider.return_value = _HybridEmbeddingProvider()
    reranker = mock_get_reranker_provider.return_value
    reranker.rerank.return_value = {2: 0.95}
    owner = _owner("rerank-top-k-owner")
    anchor = KnowledgeNote.objects.create(
        owner=owner,
        title="Anchor",
        summary_sentence="Starre Ueberzeugungen erzeugen Widerstand und kosten Energie.",
        deeper_principle="anchor principle",
    )
    strong_match = KnowledgeNote.objects.create(
        owner=owner,
        title="Strong",
        core_insight="Starre Ueberzeugungen und Widerstand binden Energie im Alltag.",
        deeper_principle="strong principle",
    )
    weak_match = KnowledgeNote.objects.create(
        owner=owner,
        title="Weak",
        core_insight="Morgenmeditation bringt Ruhe und Fokus.",
        deeper_principle="weak principle",
    )

    link_notes_by_principle(anchor.id)

    strong_candidate = KnowledgeNoteLinkCandidate.objects.get(
        source_note=anchor,
        target_note=strong_match,
    )
    weak_candidate = KnowledgeNoteLinkCandidate.objects.get(
        source_note=anchor,
        target_note=weak_match,
    )

    reranker.rerank.assert_called_once()
    rerank_candidates = reranker.rerank.call_args.args[1]
    assert [candidate["id"] for candidate in rerank_candidates] == [strong_match.id]
    assert strong_candidate.rerank_score == 0.95
    assert weak_candidate.rerank_score is None


@override_settings(
    PRINCIPLE_LINK_THRESHOLD=0.75,
    PRINCIPLE_LINK_FINAL_THRESHOLD=0.62,
    PRINCIPLE_LINK_RERANK_ENABLED=True,
    PRINCIPLE_LINK_RERANK_TOP_K=2,
)
@patch("apps.knowledge_notes.tasks.get_link_reranker_provider")
@patch("apps.knowledge_notes.providers.get_embedding_provider")
def test_reranker_failure_falls_back_to_deterministic_ranking(
    mock_get_embedding_provider,
    mock_get_reranker_provider,
):
    mock_get_embedding_provider.return_value = _HybridEmbeddingProvider()
    mock_get_reranker_provider.return_value.rerank.side_effect = RuntimeError("rerank unavailable")
    owner = _owner("rerank-fallback-owner")
    anchor = KnowledgeNote.objects.create(
        owner=owner,
        title="Anchor",
        summary_sentence="Starre Ueberzeugungen erzeugen Widerstand und kosten Energie.",
        deeper_principle="anchor principle",
    )
    strong_match = KnowledgeNote.objects.create(
        owner=owner,
        title="Strong",
        core_insight="Starre Ueberzeugungen und Widerstand binden Energie im Alltag.",
        deeper_principle="strong principle",
    )
    KnowledgeNote.objects.create(
        owner=owner,
        title="Weak",
        core_insight="Morgenmeditation bringt Ruhe und Fokus.",
        deeper_principle="weak principle",
    )

    link_notes_by_principle(anchor.id)

    anchor.refresh_from_db()
    assert list(anchor.linked_notes.values_list("id", flat=True)) == [strong_match.id]
