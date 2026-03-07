# Asegura is_trial en taller_empresa (idempotente en PostgreSQL y SQLite)
# SQLite no soporta ADD COLUMN IF NOT EXISTS, por eso usamos RunPython con lógica por vendor

from django.db import migrations, models


def add_is_trial_column(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    with schema_editor.connection.cursor() as cursor:
        if vendor == "postgresql":
            cursor.execute(
                "ALTER TABLE taller_empresa ADD COLUMN IF NOT EXISTS is_trial boolean NOT NULL DEFAULT false;"
            )
        elif vendor == "sqlite":
            cursor.execute("PRAGMA table_info(taller_empresa)")
            columns = [row[1] for row in cursor.fetchall()]
            if "is_trial" not in columns:
                cursor.execute(
                    "ALTER TABLE taller_empresa ADD COLUMN is_trial integer NOT NULL DEFAULT 0;"
                )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0081_alter_documento_payment_status"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_is_trial_column, noop_reverse),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="empresa",
                    name="is_trial",
                    field=models.BooleanField(
                        default=False,
                        help_text="Indica si la empresa está actualmente en período de prueba",
                    ),
                ),
            ],
        ),
    ]
