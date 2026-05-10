from django.contrib import admin

from .models import PlaybackProgress, Summary, Transcript, TranscriptSegment


@admin.register(PlaybackProgress)
class PlaybackProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "media_item", "status", "position_seconds", "progress_percent")
    list_filter = ("status",)
    search_fields = ("user__username", "media_item__title")


class TranscriptSegmentInline(admin.TabularInline):
    model = TranscriptSegment
    extra = 0


@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    list_display = ("media_item", "status", "provider", "language_code", "generated_at")
    list_filter = ("status", "provider", "language_code")
    search_fields = ("media_item__title", "content")
    inlines = [TranscriptSegmentInline]


@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ("media_item", "status", "kind", "provider", "generated_at")
    list_filter = ("status", "kind", "provider")
    search_fields = ("media_item__title", "content")
