from rest_framework import serializers

from .models import Category, ExternalSource, MediaAsset, MediaItem, Tag


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


class MediaAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaAsset
        fields = [
            "id",
            "origin",
            "file_format",
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


class MediaItemSerializer(serializers.ModelSerializer):
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
            "external_source",
            "published_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "created_at", "updated_at"]
