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

from .context_tags import CONTEXT_TAGS
from .models import KnowledgeNote
from .providers import get_embedding_provider
from .serializers import KnowledgeNoteSerializer
from .similarity import cosine_similarity
from .tasks import generate_knowledge_notes, link_notes_by_principle, update_note_embedding


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
                queryset = queryset.none()
            else:
                ordering = Case(
                    *[When(id=pk, then=pos) for pos, pk in enumerate(top_ids)],
                    output_field=IntegerField(),
                )
                queryset = queryset.filter(id__in=top_ids).order_by(ordering)
        elif q:
            queryset = queryset.filter(
                models.Q(title__icontains=q) | models.Q(content_markdown__icontains=q)
            )
        tag = self.request.query_params.get("tag", "").strip()
        if tag:
            all_qs = list(queryset)
            queryset = queryset.filter(
                id__in=[note.id for note in all_qs if tag in (note.context_tags or [])]
            )
        return queryset

    def perform_create(self, serializer):
        note = serializer.save(owner=self.request.user)
        update_note_embedding.delay(note.id)
        link_notes_by_principle.delay(note.id)

    def perform_update(self, serializer):
        note = serializer.save()
        update_note_embedding.delay(note.id)
        link_notes_by_principle.delay(note.id)


class RelatedNotesView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def get(self, request: Request, note_id: int) -> Response:
        try:
            note = KnowledgeNote.objects.get(id=note_id, owner=request.user)
        except KnowledgeNote.DoesNotExist:
            return Response({"detail": "Not found."}, status=http_status.HTTP_404_NOT_FOUND)

        if not note.deeper_principle.strip():
            return Response([])

        try:
            provider = get_embedding_provider()
            note_emb = provider.embed_text(note.deeper_principle)
        except Exception:
            return Response([])

        candidates = (
            KnowledgeNote.objects.filter(owner=request.user)
            .exclude(id=note_id)
            .exclude(deeper_principle="")
        )

        scored: list[dict[str, int | str | float]] = []
        for candidate in candidates:
            if not candidate.deeper_principle.strip():
                continue
            try:
                cand_emb = provider.embed_text(candidate.deeper_principle)
            except Exception:
                continue
            score = cosine_similarity(note_emb, cand_emb)
            if score > 0.1:
                scored.append(
                    {
                        "id": candidate.id,
                        "title": candidate.title,
                        "core_insight": candidate.core_insight,
                        "similarity_score": round(score, 4),
                    }
                )

        scored.sort(key=lambda item: -float(item["similarity_score"]))
        return Response(scored[:5])


class ContextTagsView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerRole]

    def get(self, request: Request) -> Response:
        return Response(CONTEXT_TAGS)


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
