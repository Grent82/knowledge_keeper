import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_knowledge_notes(self, transcript_id: int, force: bool = False) -> None:
    from apps.playback.models import ArtifactStatus, Transcript

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

    try:
        provider = get_note_provider()
        results = provider.generate(transcript_text, language_code=transcript.language_code)
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
                kind=kind,
                ai_generated=True,
                media_item=media_item,
                transcript=transcript,
            )
        )

    if notes:
        KnowledgeNote.objects.bulk_create(notes)
        logger.info("Created %d AI knowledge notes for transcript %s", len(notes), transcript_id)
    else:
        logger.warning("Note provider returned no results for transcript %s", transcript_id)
