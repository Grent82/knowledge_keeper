from rest_framework.routers import SimpleRouter

from .views import (
    CategoryVisibilityAssignmentViewSet,
    MediaItemVisibilityAssignmentViewSet,
)

router = SimpleRouter(trailing_slash=False)
router.register(
    "category-assignments",
    CategoryVisibilityAssignmentViewSet,
    basename="category-visibility-assignment",
)
router.register(
    "media-assignments",
    MediaItemVisibilityAssignmentViewSet,
    basename="media-item-visibility-assignment",
)

urlpatterns = router.urls
