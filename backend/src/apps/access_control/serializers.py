from rest_framework import serializers

from .models import CategoryVisibilityAssignment, MediaItemVisibilityAssignment


class CategoryVisibilityAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryVisibilityAssignment
        fields = ["id", "user", "category", "created_at"]
        read_only_fields = ["id", "created_at"]


class MediaItemVisibilityAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaItemVisibilityAssignment
        fields = ["id", "user", "media_item", "created_at"]
        read_only_fields = ["id", "created_at"]
