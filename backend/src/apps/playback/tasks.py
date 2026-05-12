import logging
import re
import shutil
import tempfile

from celery import shared_task
from django.utils import timezone

from .models import ArtifactStatus, Summary, Transcript, TranscriptSegment
from .ports import SegmentResult, TranscriptionResult
from .providers.factory import get_summary_provider, get_transcription_provider

logger = logging.getLogger(__name__)


def _extract_youtube_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None


def _try_youtube_captions(source_url: str):
    """Fetch YouTube captions via youtube-transcript-api v1.x."""
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import NoTranscriptFound, TranscriptsDisabled

    video_id = _extract_youtube_id(source_url)
    if not video_id:
        return None

    ytt = YouTubeTranscriptApi()
    try:
        transcript_list = ytt.list(video_id)
    except (TranscriptsDisabled, Exception):
        return None

    transcript = None
    for lang in ["de", "en"]:
        try:
            transcript = transcript_list.find_transcript([lang])
            break
        except NoTranscriptFound:
            pass

    if transcript is None:
        try:
            transcript = transcript_list.find_generated_transcript(["de", "en"])
        except Exception:
            return None

    try:
        fetched = transcript.fetch()
    except Exception:
        return None

    segments = [
        SegmentResult(
            sequence_number=i,
            content=snippet.text.replace("\n", " "),
            start_seconds=snippet.start,
            end_seconds=snippet.start + snippet.duration,
        )
        for i, snippet in enumerate(fetched)
    ]

    return TranscriptionResult(
        full_text=" ".join(s.content for s in segments),
        language_code=transcript.language_code,
        segments=segments,
    )


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
                "check_formats": "selected",
                "extractor_args": {"youtube": {"player_client": ["ios", "web"]}},
                "http_headers": {
                    "User-Agent": (
                        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                        "Version/17.0 Mobile/15E148 Safari/604.1"
                    ),
                },
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
        result = None

        # For YouTube: try captions first (fast, no DRM issues)
        if media_item.external_source_id:
            try:
                result = _try_youtube_captions(media_item.external_source.source_url)
                if result:
                    logger.info(
                        "Captions fetched for media_item %s (%d segments)",
                        media_item_id,
                        len(result.segments),
                    )
                else:
                    logger.info(
                        "No captions available for media_item %s, falling back to audio",
                        media_item_id,
                    )
            except Exception as exc:
                logger.warning("Caption fetch failed for media_item %s: %s", media_item_id, exc)

        # Fall back to audio download + Whisper
        if result is None:
            try:
                audio_path, tmpdir = _resolve_audio_path(media_item)
            except Exception as exc:
                error_msg = str(exc)
                # DRM-protected content cannot be downloaded — no point retrying
                if "DRM" in error_msg or "format is not available" in error_msg.lower():
                    logger.error(
                        "DRM/format error for media_item %s — marking FAILED (no retry)",
                        media_item_id,
                    )
                    transcript.status = ArtifactStatus.FAILED
                    transcript.error_message = (
                        "Dieses Video kann nicht transkribiert werden: "
                        "Keine Untertitel verfügbar und Audio ist DRM-geschützt."
                    )
                    transcript.save(update_fields=["status", "error_message", "updated_at"])
                    return
                raise

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

    # Idempotency: scoped to (media_item, transcript, kind) — each kind is independent.
    existing = Summary.objects.filter(
        media_item=media_item,
        transcript=transcript,
        kind=kind,
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
