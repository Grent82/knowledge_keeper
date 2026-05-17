import logging

from celery import shared_task
from django.conf import settings as django_settings
from django.utils import timezone

from .providers import get_substance_gate_provider

logger = logging.getLogger(__name__)


def _split_into_chunks(text: str, words_per_chunk: int = 500) -> list[str]:
    words = text.split()
    chunks: list[str] = []
    for index in range(0, len(words), words_per_chunk):
        chunks.append(" ".join(words[index : index + words_per_chunk]))
    return chunks


def _note_link_text(note) -> str:
    return " ".join(
        part.strip()
        for part in [
            note.title,
            note.summary_sentence,
            note.core_insight,
            note.deeper_principle,
        ]
        if part.strip()
    )


def get_link_reranker_provider():
    from .providers import get_link_reranker_provider as provider_factory

    return provider_factory()


@shared_task
def link_notes_by_principle(note_id: int) -> None:
    """Auto-link a note to others with similar deeper_principle via embedding cosine similarity."""
    from .models import KnowledgeNote, KnowledgeNoteLinkCandidate, LinkCandidateStatus
    from .providers import get_embedding_provider
    from .similarity import cosine_similarity
    from .tfidf import score_text_against_corpus

    threshold = float(getattr(django_settings, "PRINCIPLE_LINK_THRESHOLD", 0.85))
    final_threshold = float(getattr(django_settings, "PRINCIPLE_LINK_FINAL_THRESHOLD", 0.7))
    embedding_weight = float(getattr(django_settings, "PRINCIPLE_LINK_EMBEDDING_WEIGHT", 0.7))
    tfidf_weight = float(getattr(django_settings, "PRINCIPLE_LINK_TFIDF_WEIGHT", 0.3))
    rerank_enabled = bool(getattr(django_settings, "PRINCIPLE_LINK_RERANK_ENABLED", False))
    rerank_top_k = int(getattr(django_settings, "PRINCIPLE_LINK_RERANK_TOP_K", 3))
    rerank_weight = float(getattr(django_settings, "PRINCIPLE_LINK_RERANK_WEIGHT", 0.5))

    try:
        note = KnowledgeNote.objects.get(id=note_id)
    except KnowledgeNote.DoesNotExist:
        return

    if not note.deeper_principle.strip():
        return

    try:
        provider = get_embedding_provider()
        note_emb = provider.embed_text(note.deeper_principle)
    except Exception:
        return

    candidates = (
        KnowledgeNote.objects.filter(owner=note.owner)
        .exclude(id=note_id)
        .exclude(deeper_principle="")
    )
    corpus_texts = [
        _note_link_text(note),
        *[_note_link_text(candidate) for candidate in candidates],
    ]
    source_text = _note_link_text(note)

    candidate_records: list[KnowledgeNoteLinkCandidate] = []
    for candidate in candidates:
        if not candidate.deeper_principle.strip():
            continue
        try:
            cand_emb = provider.embed_text(candidate.deeper_principle)
        except Exception:
            continue
        score = cosine_similarity(note_emb, cand_emb)
        if score >= threshold:
            tfidf_score = score_text_against_corpus(
                source_text,
                _note_link_text(candidate),
                corpus_texts,
            )
            combined_score = (embedding_weight * score) + (tfidf_weight * tfidf_score)
            status = (
                LinkCandidateStatus.ACCEPTED
                if combined_score >= final_threshold
                else LinkCandidateStatus.CANDIDATE
            )
            candidate_record, _ = KnowledgeNoteLinkCandidate.objects.update_or_create(
                source_note=note,
                target_note=candidate,
                provenance="embedding.deeper_principle",
                defaults={
                    "embedding_score": score,
                    "tfidf_score": tfidf_score,
                    "combined_score": combined_score,
                    "status": status,
                },
            )
            candidate_records.append(candidate_record)

    if rerank_enabled and candidate_records:
        ranked_candidates = sorted(
            candidate_records,
            key=lambda item: item.combined_score,
            reverse=True,
        )
        top_candidates = ranked_candidates[:rerank_top_k]
        rerank_payload = [
            {
                "id": candidate.target_note_id,
                "text": _note_link_text(candidate.target_note),
                "combined_score": candidate.combined_score,
            }
            for candidate in top_candidates
        ]
        try:
            rerank_scores = get_link_reranker_provider().rerank(source_text, rerank_payload)
        except Exception:
            rerank_scores = {}
        for candidate in top_candidates:
            rerank_score = rerank_scores.get(candidate.target_note_id)
            if rerank_score is None:
                continue
            candidate.rerank_score = rerank_score
            candidate.combined_score = ((1 - rerank_weight) * candidate.combined_score) + (
                rerank_weight * rerank_score
            )
            candidate.status = (
                LinkCandidateStatus.ACCEPTED
                if candidate.combined_score >= final_threshold
                else LinkCandidateStatus.CANDIDATE
            )
            candidate.save(update_fields=["rerank_score", "combined_score", "status", "updated_at"])

    linked_ids = [
        candidate.target_note_id
        for candidate in KnowledgeNoteLinkCandidate.objects.filter(
            source_note=note,
            provenance="embedding.deeper_principle",
            status=LinkCandidateStatus.ACCEPTED,
        ).order_by("-combined_score")
    ]

    note.linked_notes.set(linked_ids)
    if linked_ids:
        logger.info(
            "Auto-linked note %d to %d notes via deeper_principle (threshold=%.2f, final=%.2f)",
            note_id,
            len(linked_ids),
            threshold,
            final_threshold,
        )


@shared_task(bind=True, max_retries=3)
def generate_knowledge_notes(self, transcript_id: int, force: bool = False) -> None:
    from apps.playback.models import ArtifactStatus, Summary, Transcript

    from .models import KnowledgeNote, NoteKind
    from .providers.openai_compatible import get_note_provider

    try:
        transcript = Transcript.objects.select_related("media_item__owner").get(id=transcript_id)
    except Transcript.DoesNotExist:
        return

    if transcript.status != ArtifactStatus.READY:
        logger.warning("generate_knowledge_notes called on non-READY transcript %s", transcript_id)
        return

    if not force and KnowledgeNote.objects.filter(
        transcript=transcript, ai_generated=True
    ).exists():
        logger.info(
            "AI notes already exist for transcript %s — skipping (use force=True to regenerate)",
            transcript_id,
        )
        return

    media_item = transcript.media_item
    owner = media_item.owner

    transcript_text = transcript.content
    if not transcript_text.strip():
        logger.warning("Transcript %s has no content — aborting note generation", transcript_id)
        return

    ready_summaries = Summary.objects.filter(
        media_item=media_item, status=ArtifactStatus.READY
    ).values("kind", "markdown_content", "content")
    summaries: dict[str, str] = {}
    for row in ready_summaries:
        body = (row["markdown_content"] or row["content"]).strip()
        if body:
            summaries[row["kind"]] = body

    try:
        provider = get_note_provider()
        gate = get_substance_gate_provider()
        threshold = getattr(django_settings, "SUBSTANCE_GATE_THRESHOLD", 6)

        chunks = _split_into_chunks(transcript_text)
        qualified_chunks: list[str] = []
        for chunk in chunks:
            score = gate.assess(chunk)
            if score >= threshold:
                qualified_chunks.append(chunk)
            else:
                logger.info(
                    "Substanz-Gate: Score %d < %d — Chunk übersprungen (transcript %s)",
                    score,
                    threshold,
                    transcript_id,
                )

        if not qualified_chunks:
            logger.warning(
                "Substanz-Gate: Alle Chunks unterhalb Schwellwert %d — keine Notizen erzeugt "
                "(transcript %s)",
                threshold,
                transcript_id,
            )
            return

        qualified_text = "\n\n".join(qualified_chunks)
        results = provider.generate(
            qualified_text,
            language_code=transcript.language_code,
            summaries=summaries or None,
        )
    except Exception as exc:
        logger.error("Note generation failed for transcript %s: %s", transcript_id, exc)
        raise self.retry(exc=exc, countdown=60) from exc

    valid_kinds = {choice[0] for choice in NoteKind.choices}
    notes = []
    for result in results:
        kind = result.kind if result.kind in valid_kinds else NoteKind.GENERAL
        notes.append(
            KnowledgeNote(
                owner=owner,
                title=result.title,
                content_markdown=result.content_markdown,
                summary_sentence=result.summary_sentence,
                source_excerpt=result.source_excerpt,
                why_it_matters=result.why_it_matters,
                problem=result.problem,
                core_insight=result.core_insight,
                application=result.application,
                first_step=result.first_step,
                deeper_principle=result.deeper_principle,
                context_tags=result.context_tags,
                kind=kind,
                ai_generated=True,
                media_item=media_item,
                transcript=transcript,
            )
        )

    if notes:
        KnowledgeNote.objects.bulk_create(notes)
        logger.info("Created %d AI knowledge notes for transcript %s", len(notes), transcript_id)
        for note in notes:
            update_note_embedding.delay(note.id)
            link_notes_by_principle.delay(note.id)
    else:
        logger.warning("Note provider returned no results for transcript %s", transcript_id)


@shared_task
def update_note_embedding(note_id: int) -> None:
    from .models import KnowledgeNote
    from .providers import get_embedding_provider

    try:
        note = KnowledgeNote.objects.get(id=note_id)
    except KnowledgeNote.DoesNotExist:
        return

    text = f"{note.title}\n{note.content_markdown}".strip()
    if not text:
        return

    try:
        provider = get_embedding_provider()
        embedding = provider.embed_text(text)
    except Exception as exc:
        logger.warning("Skipping note embedding for note %s: %s", note_id, exc)
        return

    KnowledgeNote.objects.filter(id=note_id).update(
        embedding=embedding,
        embedding_updated_at=timezone.now(),
    )
