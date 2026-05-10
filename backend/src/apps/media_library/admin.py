from django.contrib import admin

from .models import Category, ExternalSource, MediaAsset, MediaItem, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "created_by")
    search_fields = ("name",)
    list_filter = ("parent",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by")
    search_fields = ("name",)


@admin.register(ExternalSource)
class ExternalSourceAdmin(admin.ModelAdmin):
    list_display = ("provider", "title", "source_url", "external_id", "created_by")
    list_filter = ("provider",)
    search_fields = ("title", "source_url", "external_id")


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = (
        "storage_path",
        "origin",
        "file_format",
        "mime_type",
        "duration_seconds",
        "created_by",
    )
    list_filter = ("origin", "file_format")
    search_fields = ("storage_path", "mime_type")


@admin.register(MediaItem)
class MediaItemAdmin(admin.ModelAdmin):
    list_display = ("title", "media_type", "owner", "player_display_mode")
    list_filter = ("media_type", "player_display_mode")
    search_fields = ("title", "description")
    filter_horizontal = ("categories", "tags")
