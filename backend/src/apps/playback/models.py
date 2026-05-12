from django.conf import settings
from django.db import models

from apps.media_library.models import MediaItem


class PlaybackStatus(models.TextChoices):
    NOT_STARTED = "not_started", "Not Started"
    IN_PROGRESS = "in_progress", "In Progress"
    PAUSED = "paused", "Paused"
    COMPLETED = "completed", "Completed"


class ArtifactStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    READY = "ready", "Ready"
    FAILED = "failed", "Failed"


class TranscriptProvider(models.TextChoices):
    LOCAL = "local", "Local"
    OPENAI = "openai", "OpenAI"
    IMPORTED = "imported", "Imported"
    OTHER = "other", "Other"


class SummaryKind(models.TextChoices):
    SHORT = "short", "Short"
    DETAILED = "detailed", "Detailed"
    BULLET = "bullet", "Bullet"


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class PlaybackProgress(TimestampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="playback_progress_entries",
    )
    media_item = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        related_name="playback_progress_entries",
    )
    status = models.CharField(
        max_length=20,
        choices=PlaybackStatus.choices,
        default=PlaybackStatus.NOT_STARTED,
    )
    position_seconds = models.PositiveIntegerField(default=0)
    progress_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    last_accessed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "media_item"],
                name="unique_playback_progress_per_user_media_item",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.media_item_id}"


class Transcript(TimestampedModel):
    media_item = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        related_name="transcripts",
    )
    status = models.CharField(
        max_length=20,
        choices=ArtifactStatus.choices,
        default=ArtifactStatus.PENDING,
    )
    provider = models.CharField(
        max_length=20,
        choices=TranscriptProvider.choices,
        default=TranscriptProvider.LOCAL,
    )
    language_code = models.CharField(max_length=16, blank=True)
    content = models.TextField(blank=True)
    markdown_content = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Transcript:{self.media_item_id}:{self.status}"


class TranscriptSegment(TimestampedModel):
    transcript = models.ForeignKey(
        Transcript,
        on_delete=models.CASCADE,
        related_name="segments",
    )
    sequence_number = models.PositiveIntegerField()
    start_seconds = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    end_seconds = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    content = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["transcript", "sequence_number"],
                name="unique_transcript_segment_sequence",
            )
        ]
        ordering = ["sequence_number"]

    def __str__(self) -> str:
        return f"{self.transcript_id}:{self.sequence_number}"


class Summary(TimestampedModel):
    media_item = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        related_name="summaries",
    )
    transcript = models.ForeignKey(
        Transcript,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="summaries",
    )
    status = models.CharField(
        max_length=20,
        choices=ArtifactStatus.choices,
        default=ArtifactStatus.PENDING,
    )
    kind = models.CharField(
        max_length=20,
        choices=SummaryKind.choices,
        default=SummaryKind.SHORT,
    )
    provider = models.CharField(
        max_length=20,
        choices=TranscriptProvider.choices,
        default=TranscriptProvider.LOCAL,
    )
    content = models.TextField(blank=True)
    markdown_content = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Summary:{self.media_item_id}:{self.kind}"
