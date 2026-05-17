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


class LinkCandidateStatus(models.TextChoices):
    CANDIDATE = "candidate", "Candidate"
    ACCEPTED = "accepted", "Accepted"
    REJECTED = "rejected", "Rejected"


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
    problem = models.TextField(blank=True, default="")
    core_insight = models.TextField(blank=True, default="")
    application = models.TextField(blank=True, default="")
    first_step = models.TextField(blank=True, default="")
    deeper_principle = models.TextField(blank=True, default="")
    context_tags = models.JSONField(default=list, blank=True)
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
    embedding = models.JSONField(null=True, blank=True)
    embedding_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title


class KnowledgeNoteLinkCandidate(models.Model):
    source_note = models.ForeignKey(
        KnowledgeNote,
        on_delete=models.CASCADE,
        related_name="outgoing_link_candidates",
    )
    target_note = models.ForeignKey(
        KnowledgeNote,
        on_delete=models.CASCADE,
        related_name="incoming_link_candidates",
    )
    embedding_score = models.FloatField(default=0.0)
    tfidf_score = models.FloatField(default=0.0)
    combined_score = models.FloatField(default=0.0)
    rerank_score = models.FloatField(null=True, blank=True)
    provenance = models.CharField(max_length=128, default="embedding.deeper_principle")
    status = models.CharField(
        max_length=20,
        choices=LinkCandidateStatus.choices,
        default=LinkCandidateStatus.CANDIDATE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-combined_score", "-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["source_note", "target_note", "provenance"],
                name="knowledge_note_link_candidate_unique_source_target_provenance",
            ),
            models.CheckConstraint(
                condition=~models.Q(source_note=models.F("target_note")),
                name="knowledge_note_link_candidate_no_self_link",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.source_note_id}->{self.target_note_id} ({self.provenance})"
