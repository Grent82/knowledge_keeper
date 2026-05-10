from rest_framework.routers import SimpleRouter

from .views import PlaybackProgressViewSet, SummaryViewSet, TranscriptViewSet

router = SimpleRouter(trailing_slash=False)
router.register("progress", PlaybackProgressViewSet, basename="playback-progress")
router.register("transcripts", TranscriptViewSet, basename="transcript")
router.register("summaries", SummaryViewSet, basename="summary")

urlpatterns = router.urls
