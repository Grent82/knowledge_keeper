from django.db import models
from django.db.models import Case, IntegerField, When
from rest_framework import status as http_status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.common.permissions import IsOwnerRole
from apps.playback.models import ArtifactStatus, Transcript

from .models import KnowledgeNote
from .providers import get_embedding_provider
from .serializers import KnowledgeNoteSerializer
from .similarity import cosine_similarity
from .tasks import generate_knowledge_notes, update_note_embedding


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
        q = self.request.query_params.get("q", "").strip()
        semantic = self.request.query_params.get("semantic", "").lower() in ("true", "1")
        if semantic and q:
            query_embedding = get_embedding_provider().embed_text(q)
            all_notes = list(queryset.exclude(embedding=None))
            scored = [
                (note, cosine_similarity(query_embedding, note.embedding))
                for note in all_notes
            ]
            scored.sort(key=lambda item: -item[1])
            top_ids = [note.id for note, score in scored[:10] if score > 0.0]
            if not top_ids:
                return queryset.none()
            ordering = Case(
                *[When(id=pk, then=pos) for pos, pk in enumerate(top_ids)],
                output_field=IntegerField(),
            )
            return queryset.filter(id__in=top_ids).order_by(ordering)
        if q:
            queryset = queryset.filter(
                models.Q(title__icontains=q) | models.Q(content_markdown__icontains=q)
            )
        return queryset

    def perform_create(self, serializer):
        note = serializer.save(owner=self.request.user)
        update_note_embedding.delay(note.id)

    def perform_update(self, serializer):
        note = serializer.save()
        update_note_embedding.delay(note.id)


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
