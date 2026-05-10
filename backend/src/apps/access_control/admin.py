from django.contrib import admin

from .models import CategoryVisibilityAssignment, MediaItemVisibilityAssignment


@admin.register(CategoryVisibilityAssignment)
class CategoryVisibilityAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "created_at")
    search_fields = ("user__username", "category__name")


@admin.register(MediaItemVisibilityAssignment)
class MediaItemVisibilityAssignmentAdmin(admin.ModelAdmin):
    list_display = ("user", "media_item", "created_at")
    search_fields = ("user__username", "media_item__title")
