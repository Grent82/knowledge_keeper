from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import KnowledgeNoteViewSet, TriggerKnowledgeNoteGenerationView

router = SimpleRouter(trailing_slash=False)
router.register("", KnowledgeNoteViewSet, basename="knowledge-note")

urlpatterns = router.urls + [
    path(
        "generate/<int:transcript_id>/",
        TriggerKnowledgeNoteGenerationView.as_view(),
        name="trigger-knowledge-note-generation",
    ),
]
