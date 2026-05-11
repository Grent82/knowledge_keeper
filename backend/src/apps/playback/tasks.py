import shutil
import tempfile

from celery import shared_task
from django.utils import timezone

from .models import ArtifactStatus, Summary, Transcript, TranscriptSegment
from .providers.factory import get_summary_provider, get_transcription_provider


def _resolve_audio_path(media_item) -> tuple[str, str | None]:
    """Return (audio_path, tmpdir_to_cleanup).

    For local assets: returns the storage_path (relative, resolved by provider).
    For external sources (YouTube etc.): downloads audio via yt-dlp to a temp dir.
    """
    if media_item.asset_id:
        try:
            return str(media_item.asset.storage_path), None
        except Exception:
            return "", None

    if media_item.external_source_id:
        source_url = media_item.external_source.source_url
        tmpdir = tempfile.mkdtemp(prefix="kk_transcribe_")
        try:
            import yt_dlp

            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"{tmpdir}/audio.%(ext)s",
                "quiet": True,
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(source_url, download=True)
                audio_path = ydl.prepare_filename(info)
            return audio_path, tmpdir
        except Exception:
            shutil.rmtree(tmpdir, ignore_errors=True)
            raise

    return "", None


@shared_task(bind=True, max_retries=3)
def transcribe_media_item(self, media_item_id: int) -> None:
    from apps.media_library.models import MediaItem

    try:
        media_item = MediaItem.objects.get(id=media_item_id)
    except MediaItem.DoesNotExist:
        return

    existing = Transcript.objects.filter(
        media_item=media_item, status=ArtifactStatus.READY
    ).first()
    if existing:
        return

    transcript, _ = Transcript.objects.get_or_create(
        media_item=media_item,
        defaults={"status": ArtifactStatus.PENDING},
    )

    if transcript.status == ArtifactStatus.PROCESSING:
        return

    transcript.status = ArtifactStatus.PROCESSING
    transcript.save(update_fields=["status", "updated_at"])

    tmpdir = None
    try:
        audio_path, tmpdir = _resolve_audio_path(media_item)

        if not audio_path:
            transcript.status = ArtifactStatus.FAILED
            transcript.error_message = "No media file or external source attached."
            transcript.save(update_fields=["status", "error_message", "updated_at"])
            return

        result = get_transcription_provider().transcribe(audio_path)

        transcript.content = result.full_text
        transcript.language_code = result.language_code
        transcript.status = ArtifactStatus.READY
        transcript.generated_at = timezone.now()
        transcript.error_message = ""
        transcript.save(
            update_fields=[
                "content",
                "language_code",
                "status",
                "generated_at",
                "error_message",
                "updated_at",
            ]
        )

        TranscriptSegment.objects.filter(transcript=transcript).delete()
        segments = [
            TranscriptSegment(
                transcript=transcript,
                sequence_number=segment.sequence_number,
                content=segment.content,
                start_seconds=segment.start_seconds,
                end_seconds=segment.end_seconds,
            )
            for segment in result.segments
        ]
        TranscriptSegment.objects.bulk_create(segments)

        summarize_transcript.delay(transcript.id)
    except Exception as exc:
        transcript.status = ArtifactStatus.FAILED
        transcript.error_message = str(exc)
        transcript.save(update_fields=["status", "error_message", "updated_at"])
        raise self.retry(exc=exc, countdown=60) from exc
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


@shared_task(bind=True, max_retries=3)
def summarize_transcript(self, transcript_id: int, kind: str = "short") -> None:
    try:
        transcript = Transcript.objects.get(id=transcript_id)
    except Transcript.DoesNotExist:
        return

    if transcript.status != ArtifactStatus.READY:
        return

    media_item = transcript.media_item

    existing = Summary.objects.filter(
        media_item=media_item,
        transcript=transcript,
        status=ArtifactStatus.READY,
    ).first()
    if existing:
        return

    summary, _ = Summary.objects.get_or_create(
        media_item=media_item,
        transcript=transcript,
        kind=kind,
        defaults={"status": ArtifactStatus.PENDING},
    )

    if summary.status == ArtifactStatus.PROCESSING:
        return

    summary.status = ArtifactStatus.PROCESSING
    summary.save(update_fields=["status", "updated_at"])

    try:
        content = get_summary_provider().summarize(transcript.content, kind=kind)
        summary.content = content
        summary.status = ArtifactStatus.READY
        summary.generated_at = timezone.now()
        summary.error_message = ""
        summary.save(
            update_fields=["content", "status", "generated_at", "error_message", "updated_at"]
        )
    except Exception as exc:
        summary.status = ArtifactStatus.FAILED
        summary.error_message = str(exc)
        summary.save(update_fields=["status", "error_message", "updated_at"])
        raise self.retry(exc=exc, countdown=60) from exc
