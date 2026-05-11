from django.db.models import Q
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.access_control.services import visible_categories_queryset, visible_media_items_queryset
from apps.common.permissions import IsOwnerRole

from .models import ExternalSource, MediaAsset, Tag
from .serializers import (
    CategorySerializer,
    ExternalSourceSerializer,
    MediaAssetSerializer,
    MediaItemSerializer,
    SearchSuggestionSerializer,
    TagSerializer,
)


class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return visible_categories_queryset(self.request.user)

    def perform_create(self, serializer):
        if not self.request.user.is_owner:
            self.permission_denied(
                self.request,
                message="Only owner accounts can create categories.",
            )
        serializer.save(created_by=self.request.user)


class TagViewSet(ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_owner:
            return Tag.objects.filter(created_by=self.request.user)
        return Tag.objects.filter(
            media_items__in=visible_media_items_queryset(self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        if not self.request.user.is_owner:
            self.permission_denied(self.request, message="Only owner accounts can create tags.")
        serializer.save(created_by=self.request.user)


class ExternalSourceViewSet(ModelViewSet):
    serializer_class = ExternalSourceSerializer
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def get_queryset(self):
        return ExternalSource.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MediaAssetViewSet(ModelViewSet):
    serializer_class = MediaAssetSerializer
    permission_classes = [IsAuthenticated, IsOwnerRole]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        return MediaAsset.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MediaItemViewSet(ModelViewSet):
    serializer_class = MediaItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return visible_media_items_queryset(self.request.user).select_related(
            "asset",
            "external_source",
        ).prefetch_related(
            "categories",
            "tags",
        )

    def perform_create(self, serializer):
        if not self.request.user.is_owner:
            self.permission_denied(
                self.request,
                message="Only owner accounts can create media items.",
            )
        serializer.save(owner=self.request.user)


class SearchSuggestionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        visible_categories = visible_categories_queryset(request.user)
        visible_media_items = visible_media_items_queryset(request.user)
        visible_tags = (
            Tag.objects.filter(media_items__in=visible_media_items).distinct()
            if not request.user.is_owner
            else Tag.objects.filter(created_by=request.user)
        )

        if query:
            categories = visible_categories.filter(name__icontains=query)[:8]
            tags = visible_tags.filter(name__icontains=query)[:8]
            media_items = visible_media_items.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            ).select_related("asset", "external_source")[:8]
        else:
            categories = visible_categories[:8]
            tags = visible_tags[:8]
            media_items = visible_media_items.select_related("asset", "external_source")[:8]

        serializer = SearchSuggestionSerializer(
            {
                "categories": categories,
                "tags": tags,
                "media_items": media_items,
            }
        )
        return Response(serializer.data)
