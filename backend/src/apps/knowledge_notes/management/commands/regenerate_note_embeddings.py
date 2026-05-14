from django.core.management.base import BaseCommand

from apps.knowledge_notes.models import KnowledgeNote
from apps.knowledge_notes.tasks import update_note_embedding


class Command(BaseCommand):
    help = "Regenerate embeddings for all knowledge notes."

    def handle(self, *args, **options):
        ids = list(KnowledgeNote.objects.values_list("id", flat=True))
        self.stdout.write(f"Queuing embeddings for {len(ids)} notes...")
        for note_id in ids:
            update_note_embedding.delay(note_id)
        self.stdout.write(self.style.SUCCESS("Done."))
