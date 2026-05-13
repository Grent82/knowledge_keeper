from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .chat_providers import get_chat_provider
from .serializers import CoachChatRequestSerializer
from .services import retrieve_segments


class CoachChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = CoachChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data["question"]
        history = serializer.validated_data.get("history", [])

        cited_segments = retrieve_segments(question, owner=request.user, limit=5)
        answer = get_chat_provider().generate_answer(
            question=question,
            history=history,
            segments=cited_segments,
        )

        return Response(
            {
                "answer": answer,
                "cited_segments": [
                    {
                        "segment_id": segment.segment_id,
                        "media_item_id": segment.media_item_id,
                        "content": segment.content,
                        "start_seconds": segment.start_seconds,
                    }
                    for segment in cited_segments
                ],
            },
            status=status.HTTP_200_OK,
        )
