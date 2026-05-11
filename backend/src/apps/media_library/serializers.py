import re
from urllib.parse import parse_qs, urlparse

from rest_framework import serializers

from .models import Category, ExternalSource, MediaAsset, MediaItem, Tag


def _extract_youtube_id(url: str) -> str:
    """Extract YouTube video ID from various URL formats."""
    parsed = urlparse(url)
    if parsed.hostname in ("youtu.be",):
        return parsed.path.lstrip("/").split("?")[0]
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]
        # /embed/<id> or /shorts/<id>
        match = re.match(r"^/(embed|shorts|v)/([^/?&]+)", parsed.path)
        if match:
            return match.group(2)
    return ""


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "parent", "created_by", "created_at", "updated_at"]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "created_by", "created_at", "updated_at"]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class ExternalSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalSource
        fields = [
            "id",
            "provider",
            "source_url",
            "external_id",
            "title",
            "author_name",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def validate(self, attrs: dict) -> dict:
        provider = attrs.get("provider") or (self.instance.provider if self.instance else "")
        source_url = attrs.get("source_url") or (self.instance.source_url if self.instance else "")
        # Auto-extract external_id for YouTube if not provided
        if provider == "youtube" and not attrs.get("external_id") and source_url:
            attrs["external_id"] = _extract_youtube_id(source_url)
        return attrs


class MediaAssetSerializer(serializers.ModelSerializer):
    uploaded_file = serializers.FileField(write_only=True, required=False, allow_null=True)
    asset_url = serializers.CharField(read_only=True)
    filename = serializers.CharField(read_only=True)

    class Meta:
        model = MediaAsset
        fields = [
            "id",
            "origin",
            "file_format",
            "uploaded_file",
            "asset_url",
            "filename",
            "mime_type",
            "storage_path",
            "file_size_bytes",
            "duration_seconds",
            "width",
            "height",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]
        extra_kwargs = {
            "storage_path": {"required": False, "allow_blank": True},
            "mime_type": {"required": False, "allow_blank": True},
            "file_size_bytes": {"required": False},
            "duration_seconds": {"required": False},
            "width": {"required": False},
            "height": {"required": False},
        }

    def validate(self, attrs):
        uploaded_file = attrs.get("uploaded_file")
        storage_path = attrs.get("storage_path", "")
        if not uploaded_file and not storage_path:
            raise serializers.ValidationError(
                "Provide either an uploaded_file or a storage_path."
            )
        return attrs

    def create(self, validated_data):
        uploaded_file = validated_data.pop("uploaded_file", None)
        if uploaded_file is not None:
            validated_data.setdefault("mime_type", getattr(uploaded_file, "content_type", ""))
            validated_data.setdefault("file_size_bytes", uploaded_file.size)
            validated_data.setdefault("storage_path", uploaded_file.name)
        asset = MediaAsset.objects.create(uploaded_file=uploaded_file, **validated_data)
        if uploaded_file is not None:
            asset.storage_path = asset.uploaded_file.name
            asset.save(update_fields=["storage_path", "updated_at"])
        return asset


class MediaItemSerializer(serializers.ModelSerializer):
    asset_detail = MediaAssetSerializer(source="asset", read_only=True)
    external_source_detail = ExternalSourceSerializer(source="external_source", read_only=True)

    class Meta:
        model = MediaItem
        fields = [
            "id",
            "title",
            "description",
            "media_type",
            "player_display_mode",
            "owner",
            "categories",
            "tags",
            "asset",
            "asset_detail",
            "external_source",
            "external_source_detail",
            "published_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]


class SearchSuggestionSerializer(serializers.Serializer):
    categories = CategorySerializer(many=True)
    tags = TagSerializer(many=True)
    media_items = MediaItemSerializer(many=True)
