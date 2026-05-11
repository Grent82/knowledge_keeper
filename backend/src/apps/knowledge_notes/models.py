from django.conf import settings
from django.db import models

from apps.media_library.models import MediaItem
from apps.playback.models import Transcript


class KnowledgeNote(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="knowledge_notes",
    )
    title = models.CharField(max_length=255)
    content_markdown = models.TextField(blank=True)
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
