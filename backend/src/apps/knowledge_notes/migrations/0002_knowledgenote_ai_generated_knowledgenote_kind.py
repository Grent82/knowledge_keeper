from django.db import migrations, models


NOTE_KIND_CHOICES = [
    ("insight", "Insight"),
    ("action", "Action"),
    ("reflection", "Reflection"),
    ("question", "Question"),
    ("general", "General"),
]


def _column_names(schema_editor, table_name: str) -> set[str]:
    with schema_editor.connection.cursor() as cursor:
        description = schema_editor.connection.introspection.get_table_description(
            cursor, table_name
        )
    return {column.name for column in description}


def _field_definitions() -> list[tuple[str, models.Field]]:
    return [
        ("ai_generated", models.BooleanField(default=False)),
        (
            "kind",
            models.CharField(
                choices=NOTE_KIND_CHOICES,
                default="general",
                max_length=20,
            ),
        ),
    ]


def _quote_table_name(schema_editor, table_name: str) -> str:
    return schema_editor.quote_name(table_name)


def _add_missing_fields_for_model(schema_editor, model) -> None:
    table_name = _quote_table_name(schema_editor, model._meta.db_table)
    columns = _column_names(schema_editor, model._meta.db_table)

    if "ai_generated" not in columns:
        schema_editor.execute(
            f"ALTER TABLE {table_name} "
            "ADD COLUMN ai_generated bool NOT NULL DEFAULT false"
        )
        columns.add("ai_generated")

    if "kind" not in columns:
        schema_editor.execute(
            f"ALTER TABLE {table_name} "
            "ADD COLUMN kind varchar(20) NOT NULL DEFAULT 'general'"
        )
        columns.add("kind")


def _remove_existing_fields_for_model(schema_editor, model) -> None:
    table_name = _quote_table_name(schema_editor, model._meta.db_table)
    columns = _column_names(schema_editor, model._meta.db_table)

    if "kind" in columns:
        schema_editor.execute(f"ALTER TABLE {table_name} DROP COLUMN kind")
        columns.remove("kind")

    if "ai_generated" in columns:
        schema_editor.execute(f"ALTER TABLE {table_name} DROP COLUMN ai_generated")
        columns.remove("ai_generated")


def _apply_missing_knowledge_note_fields(apps, schema_editor) -> None:
    model = apps.get_model("knowledge_notes", "KnowledgeNote")
    _add_missing_fields_for_model(schema_editor, model)


def _rollback_knowledge_note_fields(apps, schema_editor) -> None:
    model = apps.get_model("knowledge_notes", "KnowledgeNote")
    _remove_existing_fields_for_model(schema_editor, model)


class Migration(migrations.Migration):
    dependencies = [
        ("knowledge_notes", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="knowledgenote",
                    name="ai_generated",
                    field=models.BooleanField(default=False),
                ),
                migrations.AddField(
                    model_name="knowledgenote",
                    name="kind",
                    field=models.CharField(
                        choices=NOTE_KIND_CHOICES,
                        default="general",
                        max_length=20,
                    ),
                ),
            ],
            database_operations=[
                migrations.RunPython(
                    _apply_missing_knowledge_note_fields,
                    reverse_code=_rollback_knowledge_note_fields,
                )
            ],
        ),
    ]
