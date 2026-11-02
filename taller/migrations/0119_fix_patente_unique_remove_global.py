"""
Producción (PostgreSQL) tiene un índice UNIQUE legacy solo en patente (sin empresa_id),
creado antes de que se migrara a UniqueConstraint(empresa, patente).
Elimina ese índice/constraint y garantiza que solo exista uq_empresa_patente.
SQLite (dev local) no tiene el problema — el bloque es no-op allí.
"""
from django.db import migrations


def fix_patente_unique_constraint(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return

    with schema_editor.connection.cursor() as cursor:
        # 1. Buscar y eliminar cualquier índice UNIQUE sobre patente solo (sin empresa_id)
        cursor.execute(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'taller_vehiculo'
              AND indexdef ILIKE '%%unique%%'
              AND indexdef ILIKE '%%patente%%'
              AND indexdef NOT ILIKE '%%empresa%%'
            """
        )
        for (idx_name,) in cursor.fetchall():
            cursor.execute(f'DROP INDEX IF EXISTS "{idx_name}"')

        # 2. Eliminar constraint de tabla (ej. taller_vehiculo_patente_key) si existe
        cursor.execute(
            """
            SELECT conname
            FROM pg_constraint
            WHERE conrelid = 'taller_vehiculo'::regclass
              AND contype = 'u'
              AND conname != 'uq_empresa_patente'
              AND array_to_string(
                    ARRAY(
                      SELECT attname FROM pg_attribute
                      WHERE attrelid = conrelid
                        AND attnum = ANY(conkey)
                    ), ','
                  ) = 'patente'
            """
        )
        for (con_name,) in cursor.fetchall():
            cursor.execute(
                f'ALTER TABLE taller_vehiculo DROP CONSTRAINT IF EXISTS "{con_name}"'
            )

        # 3. Asegurar que uq_empresa_patente exista
        cursor.execute(
            """
            SELECT COUNT(*) FROM pg_constraint
            WHERE conname = 'uq_empresa_patente'
              AND conrelid = 'taller_vehiculo'::regclass
            """
        )
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "ALTER TABLE taller_vehiculo"
                " ADD CONSTRAINT uq_empresa_patente UNIQUE (empresa_id, patente)"
            )


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0118_vehiculoimagen"),
    ]

    operations = [
        migrations.RunPython(
            fix_patente_unique_constraint,
            migrations.RunPython.noop,
        ),
    ]
