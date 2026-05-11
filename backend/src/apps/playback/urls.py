from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
    PlaybackProgressViewSet,
    SummaryViewSet,
    TranscriptSegmentViewSet,
    TranscriptViewSet,
    TriggerTranscriptionView,
)

router = SimpleRouter(trailing_slash=False)
router.register("progress", PlaybackProgressViewSet, basename="playback-progress")
router.register("transcripts", TranscriptViewSet, basename="transcript")
router.register("summaries", SummaryViewSet, basename="summary")
router.register("segments", TranscriptSegmentViewSet, basename="transcript-segment")

urlpatterns = router.urls + [
    path(
        "trigger/<int:media_item_id>/",
        TriggerTranscriptionView.as_view(),
        name="trigger-transcription",
    ),
]
