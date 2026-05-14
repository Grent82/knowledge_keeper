from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import (
    ContextTagsView,
    KnowledgeNoteViewSet,
    RelatedNotesView,
    TriggerKnowledgeNoteGenerationView,
)

router = SimpleRouter(trailing_slash=False)
router.register("", KnowledgeNoteViewSet, basename="knowledge-note")

urlpatterns = [
    path(
        "context-tags/",
        ContextTagsView.as_view(),
        name="knowledge-notes-context-tags",
    ),
    path(
        "<int:note_id>/related/",
        RelatedNotesView.as_view(),
        name="knowledge-note-related",
    ),
    *router.urls,
    path(
        "generate/<int:transcript_id>/",
        TriggerKnowledgeNoteGenerationView.as_view(),
        name="trigger-knowledge-note-generation",
    ),
]
