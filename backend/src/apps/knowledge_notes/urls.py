from rest_framework.routers import SimpleRouter

from .views import KnowledgeNoteViewSet

router = SimpleRouter(trailing_slash=False)
router.register("", KnowledgeNoteViewSet, basename="knowledge-note")
urlpatterns = router.urls
