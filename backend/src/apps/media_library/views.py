from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.access_control.services import visible_categories_queryset, visible_media_items_queryset
from apps.common.permissions import IsOwnerRole

from .models import ExternalSource, MediaAsset, Tag
from .serializers import (
    CategorySerializer,
    ExternalSourceSerializer,
    MediaAssetSerializer,
    MediaItemSerializer,
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
