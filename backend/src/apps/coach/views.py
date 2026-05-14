from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.knowledge_notes.models import KnowledgeNote
from apps.knowledge_notes.providers import get_embedding_provider
from apps.knowledge_notes.similarity import cosine_similarity

from .chat_providers import get_chat_provider
from .serializers import CoachChatRequestSerializer
from .services import retrieve_segments


def _retrieve_relevant_notes(question: str, owner, limit: int = 3) -> list[dict]:
    """Return top-k knowledge notes ranked by embedding similarity to question."""
    try:
        query_emb = get_embedding_provider().embed_text(question)
    except Exception:
        return []

    notes = list(KnowledgeNote.objects.filter(owner=owner).exclude(embedding=None))
    scored = [(note, cosine_similarity(query_emb, note.embedding)) for note in notes]
    scored.sort(key=lambda item: -item[1])
    return [
        {
            "note_id": note.id,
            "title": note.title,
            "summary": note.summary_sentence,
            "score": round(score, 4),
        }
        for note, score in scored[:limit]
        if score > 0.1
    ]


class CoachChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = CoachChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data["question"]
        context_tag = serializer.validated_data.get("context_tag", "")
        history = serializer.validated_data.get("history", [])

        retrieval_query = f"{question} {context_tag}".strip() if context_tag else question
        cited_segments = retrieve_segments(retrieval_query, owner=request.user, limit=5)
        relevant_notes = _retrieve_relevant_notes(retrieval_query, owner=request.user)
        coach_answer = get_chat_provider().generate_answer(
            question=question,
            history=history,
            segments=cited_segments,
        )

        return Response(
            {
                "answer": coach_answer.answer,
                "response_mode": coach_answer.mode,
                "source_semantics": "related_sources",
                "context_tag": context_tag,
                "cited_segments": [
                    {
                        "segment_id": segment.segment_id,
                        "media_item_id": segment.media_item_id,
                        "snippet": segment.snippet,
                        "start_seconds": segment.start_seconds,
                    }
                    for segment in cited_segments
                ],
                "relevant_notes": relevant_notes,
            },
            status=status.HTTP_200_OK,
        )
