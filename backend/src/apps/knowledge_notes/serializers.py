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
            "media_item",
            "transcript",
            "linked_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]
