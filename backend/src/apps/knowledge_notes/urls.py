from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import ContextTagsView, KnowledgeNoteViewSet, TriggerKnowledgeNoteGenerationView

router = SimpleRouter(trailing_slash=False)
router.register("", KnowledgeNoteViewSet, basename="knowledge-note")

urlpatterns = [
    path(
        "context-tags/",
        ContextTagsView.as_view(),
        name="knowledge-notes-context-tags",
    ),
    *router.urls,
    path(
        "generate/<int:transcript_id>/",
        TriggerKnowledgeNoteGenerationView.as_view(),
        name="trigger-knowledge-note-generation",
    ),
]
