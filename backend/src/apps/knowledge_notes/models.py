from django.conf import settings
from django.db import models

from apps.media_library.models import MediaItem
from apps.playback.models import Transcript


class NoteKind(models.TextChoices):
    INSIGHT = "insight", "Insight"
    ACTION = "action", "Action"
    REFLECTION = "reflection", "Reflection"
    QUESTION = "question", "Question"
    GENERAL = "general", "General"


class KnowledgeNote(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="knowledge_notes",
    )
    title = models.CharField(max_length=255)
    content_markdown = models.TextField(blank=True)
    summary_sentence = models.TextField(blank=True)
    source_excerpt = models.TextField(blank=True)
    why_it_matters = models.TextField(blank=True)
    kind = models.CharField(
        max_length=20,
        choices=NoteKind.choices,
        default=NoteKind.GENERAL,
    )
    ai_generated = models.BooleanField(default=False)
    media_item = models.ForeignKey(
        MediaItem,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="knowledge_notes",
    )
    transcript = models.ForeignKey(
        Transcript,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="knowledge_notes",
    )
    linked_notes = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="linked_from",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title
