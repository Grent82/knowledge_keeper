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


@shared_task
def link_notes_by_principle(note_id: int) -> None:
    """Auto-link a note to others with similar deeper_principle via embedding cosine similarity."""
    from .models import KnowledgeNote
    from .providers import get_embedding_provider
    from .similarity import cosine_similarity

    threshold = float(getattr(django_settings, "PRINCIPLE_LINK_THRESHOLD", 0.85))

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

    linked_ids: list[int] = []
    for candidate in candidates:
        if not candidate.deeper_principle.strip():
            continue
        try:
            cand_emb = provider.embed_text(candidate.deeper_principle)
        except Exception:
            continue
        score = cosine_similarity(note_emb, cand_emb)
        if score >= threshold:
            linked_ids.append(candidate.id)

    if linked_ids:
        note.linked_notes.add(*linked_ids)
        logger.info(
            "Auto-linked note %d to %d notes via deeper_principle (threshold=%.2f)",
            note_id,
            len(linked_ids),
            threshold,
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

    existing_signatures: set[tuple[str, str]] = set(
        KnowledgeNote.objects.filter(owner=owner, ai_generated=True)
        .values_list("kind", "title")
        .iterator()
    )

    valid_kinds = {choice[0] for choice in NoteKind.choices}
    notes = []
    for result in results:
        kind = result.kind if result.kind in valid_kinds else NoteKind.GENERAL
        if (kind, result.title) in existing_signatures:
            logger.info(
                "Skipping note '%s' (%s) — already exists for owner %s",
                result.title,
                kind,
                owner.id,
            )
            continue
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

    provider = get_embedding_provider()
    embedding = provider.embed_text(text)
    KnowledgeNote.objects.filter(id=note_id).update(
        embedding=embedding,
        embedding_updated_at=timezone.now(),
    )
