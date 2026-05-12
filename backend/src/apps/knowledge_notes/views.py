from rest_framework import status as http_status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.common.permissions import IsOwnerRole
from apps.playback.models import ArtifactStatus, Transcript

from .models import KnowledgeNote
from .serializers import KnowledgeNoteSerializer
from .tasks import generate_knowledge_notes


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


class TriggerKnowledgeNoteGenerationView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def post(self, request: Request, transcript_id: int) -> Response:
        force = bool(request.data.get("force", False))

        try:
            transcript = Transcript.objects.select_related("media_item").get(
                id=transcript_id,
                media_item__owner=request.user,
            )
        except Transcript.DoesNotExist:
            return Response({"detail": "Not found."}, status=http_status.HTTP_404_NOT_FOUND)

        if transcript.status != ArtifactStatus.READY:
            return Response(
                {"detail": "Transcript is not ready yet."},
                status=http_status.HTTP_409_CONFLICT,
            )

        if not force and KnowledgeNote.objects.filter(
            transcript=transcript, ai_generated=True
        ).exists():
            return Response(
                {"status": "exists", "transcript_id": transcript_id},
                status=http_status.HTTP_200_OK,
            )

        generate_knowledge_notes.delay(transcript_id, force=force)
        return Response(
            {"status": "queued", "transcript_id": transcript_id},
            status=http_status.HTTP_202_ACCEPTED,
        )
