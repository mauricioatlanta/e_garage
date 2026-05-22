"""
En producción (PostgreSQL) cliente_id en taller_vehiculo quedó NOT NULL por drift entre
migraciones y el estado real de la DB. La migración 0075 ya declaró null=True en el
modelo, pero el constraint NOT NULL persistió en la DB y se corrigió manualmente.
Este RunPython lo garantiza de forma idempotente para cualquier despliegue futuro.
SQLite (dev local) no tiene el problema — el bloque es no-op allí.
"""
from django.db import migrations


def ensure_cliente_nullable(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT is_nullable
            FROM information_schema.columns
            WHERE table_name = 'taller_vehiculo'
              AND column_name = 'cliente_id'
            """
        )
        row = cursor.fetchone()
        if row and row[0] == "NO":
            cursor.execute(
                "ALTER TABLE taller_vehiculo ALTER COLUMN cliente_id DROP NOT NULL"
            )


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0119_fix_patente_unique_remove_global"),
    ]

    operations = [
        migrations.RunPython(
            ensure_cliente_nullable,
            migrations.RunPython.noop,
        ),
    ]
