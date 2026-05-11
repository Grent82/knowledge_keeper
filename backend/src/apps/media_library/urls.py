from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
    CategoryViewSet,
    ExternalSourceViewSet,
    MediaAssetViewSet,
    MediaItemViewSet,
    SearchSuggestionView,
    TagViewSet,
)

router = SimpleRouter(trailing_slash=False)
router.register("categories", CategoryViewSet, basename="category")
router.register("tags", TagViewSet, basename="tag")
router.register("sources", ExternalSourceViewSet, basename="external-source")
router.register("assets", MediaAssetViewSet, basename="media-asset")
router.register("items", MediaItemViewSet, basename="media-item")

urlpatterns = [
    path("search", SearchSuggestionView.as_view(), name="media-search-suggestions"),
    *router.urls,
]
