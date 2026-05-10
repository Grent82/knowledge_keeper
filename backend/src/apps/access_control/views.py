from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.common.permissions import IsOwnerRole

from .models import CategoryVisibilityAssignment, MediaItemVisibilityAssignment
from .serializers import (
    CategoryVisibilityAssignmentSerializer,
    MediaItemVisibilityAssignmentSerializer,
)


class CategoryVisibilityAssignmentViewSet(ModelViewSet):
    serializer_class = CategoryVisibilityAssignmentSerializer
    permission_classes = [IsAuthenticated, IsOwnerRole]
    queryset = CategoryVisibilityAssignment.objects.select_related("user", "category")


class MediaItemVisibilityAssignmentViewSet(ModelViewSet):
    serializer_class = MediaItemVisibilityAssignmentSerializer
    permission_classes = [IsAuthenticated, IsOwnerRole]
    queryset = MediaItemVisibilityAssignment.objects.select_related("user", "media_item")
