from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.common.permissions import IsOwnerRole

from .models import KnowledgeNote
from .serializers import KnowledgeNoteSerializer


class KnowledgeNoteViewSet(ModelViewSet):
    serializer_class = KnowledgeNoteSerializer
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def get_queryset(self):
        queryset = KnowledgeNote.objects.filter(owner=self.request.user).prefetch_related(
            "linked_notes"
        )
        media_item_id = self.request.query_params.get("media_item")
        if media_item_id:
            queryset = queryset.filter(media_item_id=media_item_id)
        transcript_id = self.request.query_params.get("transcript")
        if transcript_id:
            queryset = queryset.filter(transcript_id=transcript_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
