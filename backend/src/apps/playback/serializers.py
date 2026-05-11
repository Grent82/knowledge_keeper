from rest_framework import serializers

from .models import PlaybackProgress, Summary, Transcript, TranscriptSegment


class PlaybackProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaybackProgress
        fields = [
            "id",
            "user",
            "media_item",
            "status",
            "position_seconds",
            "progress_percent",
            "last_accessed_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]


class TranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcript
        fields = [
            "id",
            "media_item",
            "status",
            "provider",
            "language_code",
            "content",
            "markdown_content",
            "error_message",
            "generated_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class TranscriptSegmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranscriptSegment
        fields = [
            "id",
            "transcript",
            "sequence_number",
            "start_seconds",
            "end_seconds",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Summary
        fields = [
            "id",
            "media_item",
            "transcript",
            "status",
            "kind",
            "provider",
            "content",
            "markdown_content",
            "error_message",
            "generated_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
