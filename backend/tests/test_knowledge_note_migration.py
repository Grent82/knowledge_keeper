from importlib import import_module

import pytest
from django.db import connection, models

pytestmark = pytest.mark.django_db(transaction=True)


def test_migration_0002_is_idempotent_when_ai_generated_already_exists():
    migration = import_module(
        "apps.knowledge_notes.migrations.0002_knowledgenote_ai_generated_knowledgenote_kind"
    )

    class LegacyKnowledgeNote(models.Model):
        title = models.CharField(max_length=255)

        class Meta:
            app_label = "knowledge_notes"
            db_table = "tmp_knowledge_note_migration"

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(LegacyKnowledgeNote)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"ALTER TABLE {LegacyKnowledgeNote._meta.db_table} "
                "ADD COLUMN ai_generated bool NOT NULL DEFAULT false"
            )

        with connection.schema_editor() as schema_editor:
            migration._add_missing_fields_for_model(schema_editor, LegacyKnowledgeNote)
            migration._add_missing_fields_for_model(schema_editor, LegacyKnowledgeNote)

        with connection.cursor() as cursor:
            description = connection.introspection.get_table_description(
                cursor, LegacyKnowledgeNote._meta.db_table
            )
        column_names = {column.name for column in description}

        assert "ai_generated" in column_names
        assert "kind" in column_names
    finally:
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(LegacyKnowledgeNote)
