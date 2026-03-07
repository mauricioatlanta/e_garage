# Arregla: ValueError Found wrong number (0) of constraints for taller_documentsequence(empresa_id, tipo)
# La BD de producción puede no tener el constraint (empresa, tipo) por historial divergente.
# Esta migración elimina el constraint solo si existe (PostgreSQL) para permitir que 0080 aplique.
# Para SQLite: no-op (SQLite no usa constraints con nombre para unique_together).

from django.db import migrations


def drop_old_constraint_if_exists(apps, schema_editor):
    """Elimina el unique(empresa_id, tipo) solo si existe (PostgreSQL)."""
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            DO $$
            DECLARE
              r RECORD;
            BEGIN
              FOR r IN (
                SELECT conname FROM pg_constraint
                WHERE conrelid = 'taller_documentsequence'::regclass
                AND contype = 'u'
                AND array_length(conkey, 1) = 2
              ) LOOP
                EXECUTE format('ALTER TABLE taller_documentsequence DROP CONSTRAINT IF EXISTS %I', r.conname);
                EXIT;
              END LOOP;
            EXCEPTION WHEN undefined_table THEN
              NULL;
            END $$;
            """
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0078_merge_0075_0077"),
    ]

    operations = [
        migrations.RunPython(drop_old_constraint_if_exists, noop_reverse),
    ]
