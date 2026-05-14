from rest_framework import serializers

from .models import KnowledgeNote


class KnowledgeNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeNote
        fields = [
            "id",
            "owner",
            "title",
            "content_markdown",
            "summary_sentence",
            "source_excerpt",
            "why_it_matters",
            "problem",
            "core_insight",
            "application",
            "first_step",
            "deeper_principle",
            "context_tags",
            "kind",
            "ai_generated",
            "media_item",
            "transcript",
            "linked_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "ai_generated", "created_at", "updated_at"]
