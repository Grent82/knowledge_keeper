from rest_framework import status as http_status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.access_control.services import visible_media_items_queryset
from apps.common.permissions import IsOwnerRole
from apps.media_library.models import MediaItem

from .models import (
    ArtifactStatus,
    PlaybackProgress,
    Summary,
    SummaryKind,
    Transcript,
    TranscriptSegment,
)
from .serializers import (
    PlaybackProgressSerializer,
    SummarySerializer,
    TranscriptSegmentSerializer,
    TranscriptSerializer,
)
from .tasks import summarize_transcript, transcribe_media_item


class PlaybackProgressViewSet(ModelViewSet):
    serializer_class = PlaybackProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PlaybackProgress.objects.filter(user=self.request.user).select_related("media_item")

    def perform_create(self, serializer):
        media_item = serializer.validated_data["media_item"]
        if not visible_media_items_queryset(self.request.user).filter(id=media_item.id).exists():
            self.permission_denied(
                self.request,
                message="You cannot create playback progress for inaccessible media.",
            )
        serializer.save(user=self.request.user)


class TranscriptViewSet(ModelViewSet):
    serializer_class = TranscriptSerializer
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def get_queryset(self):
        queryset = Transcript.objects.filter(media_item__owner=self.request.user).select_related(
            "media_item"
        )
        media_item_id = self.request.query_params.get("media_item")
        if media_item_id:
            queryset = queryset.filter(media_item_id=media_item_id)
        return queryset

    def perform_create(self, serializer):
        media_item = serializer.validated_data["media_item"]
        if media_item.owner_id != self.request.user.id:
            self.permission_denied(self.request, message="Only the owner can create artifacts.")
        serializer.save()


class SummaryViewSet(ModelViewSet):
    serializer_class = SummarySerializer
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def get_queryset(self):
        queryset = Summary.objects.filter(media_item__owner=self.request.user).select_related(
            "media_item", "transcript"
        )
        media_item_id = self.request.query_params.get("media_item")
        if media_item_id:
            queryset = queryset.filter(media_item_id=media_item_id)
        return queryset

    def perform_create(self, serializer):
        media_item: MediaItem = serializer.validated_data["media_item"]
        if media_item.owner_id != self.request.user.id:
            self.permission_denied(self.request, message="Only the owner can create artifacts.")
        serializer.save()


class TranscriptSegmentViewSet(ModelViewSet):
    serializer_class = TranscriptSegmentSerializer
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def get_queryset(self):
        queryset = TranscriptSegment.objects.filter(
            transcript__media_item__owner=self.request.user
        ).select_related("transcript")
        transcript_id = self.request.query_params.get("transcript")
        if transcript_id:
            queryset = queryset.filter(transcript_id=transcript_id)
        return queryset.order_by("sequence_number")


class TriggerTranscriptionView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def post(self, request: Request, media_item_id: int) -> Response:
        try:
            media_item = MediaItem.objects.get(id=media_item_id, owner=request.user)
        except MediaItem.DoesNotExist:
            return Response({"detail": "Not found."}, status=http_status.HTTP_404_NOT_FOUND)

        if Transcript.objects.filter(
            media_item=media_item,
            status=ArtifactStatus.PROCESSING,
        ).exists():
            return Response(
                {"detail": "Transcription already in progress."},
                status=http_status.HTTP_409_CONFLICT,
            )

        transcribe_media_item.delay(media_item.id)
        return Response(
            {"status": "queued", "media_item_id": media_item.id},
            status=http_status.HTTP_202_ACCEPTED,
        )


class TriggerSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def post(self, request: Request, media_item_id: int) -> Response:
        kind = request.data.get("kind", SummaryKind.SHORT)
        if kind not in SummaryKind.values:
            return Response(
                {"detail": f"Invalid kind. Choices: {', '.join(SummaryKind.values)}"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        try:
            media_item = MediaItem.objects.get(id=media_item_id, owner=request.user)
        except MediaItem.DoesNotExist:
            return Response({"detail": "Not found."}, status=http_status.HTTP_404_NOT_FOUND)

        transcript = (
            Transcript.objects.filter(media_item=media_item, status=ArtifactStatus.READY)
            .order_by("-created_at")
            .first()
        )
        if transcript is None:
            return Response(
                {"detail": "No ready transcript found for this media item."},
                status=http_status.HTTP_409_CONFLICT,
            )

        existing = Summary.objects.filter(
            media_item=media_item,
            transcript=transcript,
            kind=kind,
            status=ArtifactStatus.READY,
        ).first()
        if existing:
            return Response(
                {"status": "ready", "summary_id": existing.id, "kind": kind},
                status=http_status.HTTP_200_OK,
            )

        in_progress = Summary.objects.filter(
            media_item=media_item,
            transcript=transcript,
            kind=kind,
            status=ArtifactStatus.PROCESSING,
        ).exists()
        if in_progress:
            return Response(
                {"detail": f"Summary of kind '{kind}' is already being generated."},
                status=http_status.HTTP_409_CONFLICT,
            )

        summarize_transcript.delay(transcript.id, kind=kind)
        return Response(
            {"status": "queued", "media_item_id": media_item.id, "kind": kind},
            status=http_status.HTTP_202_ACCEPTED,
        )
