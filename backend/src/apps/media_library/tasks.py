import logging

from celery import shared_task

from apps.media_library.models import MediaItem, Tag
from apps.media_library.providers.tagging import get_tagging_provider
from apps.playback.models import ArtifactStatus, Summary, SummaryKind, Transcript

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def auto_tag_media_item(self, media_item_id: int) -> None:
    """Derive and apply 3-5 German tags to a media item after its short summary is READY.

    Source priority: short Summary.content → Transcript.content fallback.
    Tag matching is case-insensitive against existing global Tag records.
    Existing manual tags are preserved; operation is idempotent.
    """
    try:
        media_item = MediaItem.objects.get(id=media_item_id)
    except MediaItem.DoesNotExist:
        return

    # Determine source text: short summary preferred, transcript as fallback.
    source_text = ""
    short_summary = (
        Summary.objects.filter(
            media_item=media_item,
            kind=SummaryKind.SHORT,
            status=ArtifactStatus.READY,
        )
        .order_by("-created_at")
        .first()
    )
    if short_summary and short_summary.content.strip():
        source_text = short_summary.content
    else:
        transcript = (
            Transcript.objects.filter(
                media_item=media_item,
                status=ArtifactStatus.READY,
            )
            .order_by("-created_at")
            .first()
        )
        if transcript and transcript.content.strip():
            source_text = transcript.content

    if not source_text:
        logger.warning(
            "auto_tag_media_item: no source text for media_item %s — skipping", media_item_id
        )
        return

    try:
        proposed_names = get_tagging_provider().suggest_tags(source_text)
    except Exception as exc:
        logger.error(
            "auto_tag_media_item: provider error for media_item %s: %s", media_item_id, exc
        )
        raise self.retry(exc=exc, countdown=60) from exc

    for raw_name in proposed_names:
        normalized = raw_name.strip().lower()
        if not normalized:
            continue

        # Reuse existing global Tag if name matches case-insensitively.
        tag = Tag.objects.filter(name__iexact=normalized).first()
        if tag is None:
            tag, _ = Tag.objects.get_or_create(
                name=normalized,
                defaults={"created_by": media_item.owner},
            )

        # M2M add() is idempotent — safe to call even if already present.
        media_item.tags.add(tag)

    logger.info(
        "auto_tag_media_item: applied %d tag(s) to media_item %s",
        len(proposed_names),
        media_item_id,
    )
