from rest_framework.routers import SimpleRouter

from .views import (
    PlaybackProgressViewSet,
    SummaryViewSet,
    TranscriptSegmentViewSet,
    TranscriptViewSet,
)

router = SimpleRouter(trailing_slash=False)
router.register("progress", PlaybackProgressViewSet, basename="playback-progress")
router.register("transcripts", TranscriptViewSet, basename="transcript")
router.register("summaries", SummaryViewSet, basename="summary")
router.register("segments", TranscriptSegmentViewSet, basename="transcript-segment")

urlpatterns = router.urls
