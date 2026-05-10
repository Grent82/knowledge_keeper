from django.conf import settings
from django.db import models

from apps.media_library.models import Category, MediaItem


class CategoryVisibilityAssignment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="category_visibility_assignments",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="visibility_assignments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "category"],
                name="unique_category_visibility_assignment",
            )
        ]


class MediaItemVisibilityAssignment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="media_item_visibility_assignments",
    )
    media_item = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        related_name="visibility_assignments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "media_item"],
                name="unique_media_item_visibility_assignment",
            )
        ]
