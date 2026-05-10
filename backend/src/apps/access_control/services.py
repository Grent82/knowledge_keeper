from django.db.models import Q, QuerySet

from apps.media_library.models import Category, MediaItem

from .models import CategoryVisibilityAssignment, MediaItemVisibilityAssignment


def visible_categories_queryset(user) -> QuerySet[Category]:
    if user.is_owner:
        return Category.objects.filter(created_by=user)
    return Category.objects.filter(visibility_assignments__user=user).distinct()


def visible_media_items_queryset(user) -> QuerySet[MediaItem]:
    if user.is_owner:
        return MediaItem.objects.filter(owner=user).distinct()

    direct_ids = MediaItemVisibilityAssignment.objects.filter(user=user).values("media_item_id")
    category_ids = CategoryVisibilityAssignment.objects.filter(user=user).values("category_id")
    return MediaItem.objects.filter(
        Q(id__in=direct_ids) | Q(categories__id__in=category_ids)
    ).distinct()
