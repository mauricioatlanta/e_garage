from django.db import migrations


TABLE_NAME = "taller_linearepuesto"


def align_linearepuesto_desarme_columns(apps, schema_editor):
    connection = schema_editor.connection

    with connection.cursor() as cursor:
        tables = set(connection.introspection.table_names(cursor))
        if TABLE_NAME not in tables:
            return

        columns = {
            column.name
            for column in connection.introspection.get_table_description(cursor, TABLE_NAME)
        }

        if "pieza_desarme_id" not in columns:
            cursor.execute(
                "ALTER TABLE taller_linearepuesto ADD COLUMN pieza_desarme_id bigint NULL"
            )
            columns.add("pieza_desarme_id")

        if "costo_linea" not in columns:
            cursor.execute(
                "ALTER TABLE taller_linearepuesto ADD COLUMN costo_linea numeric(12, 2) NULL"
            )
            columns.add("costo_linea")

        if "origen_repuesto" not in columns:
            cursor.execute(
                "ALTER TABLE taller_linearepuesto ADD COLUMN origen_repuesto varchar(20) NULL"
            )
            columns.add("origen_repuesto")

        cursor.execute(
            """
            UPDATE taller_linearepuesto
            SET origen_repuesto = CASE
                WHEN pieza_desarme_id IS NOT NULL THEN 'DESARME'
                WHEN repuesto_id IS NULL AND part_id IS NULL THEN 'EXTERNO'
                ELSE 'STOCK_BODEGA'
            END
            WHERE origen_repuesto IS NULL OR origen_repuesto = ''
            """
        )

        if connection.vendor == "postgresql":
            cursor.execute(
                """
                ALTER TABLE taller_linearepuesto
                ALTER COLUMN origen_repuesto SET DEFAULT 'STOCK_BODEGA'
                """
            )
            cursor.execute(
                """
                ALTER TABLE taller_linearepuesto
                ALTER COLUMN origen_repuesto SET NOT NULL
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS taller_linearepuesto_origen_repuesto_7ef0f6_idx
                ON taller_linearepuesto (origen_repuesto)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS taller_linearepuesto_pieza_desarme_id_idx
                ON taller_linearepuesto (pieza_desarme_id)
                """
            )
        elif connection.vendor == "sqlite":
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS taller_linearepuesto_origen_repuesto_7ef0f6_idx
                ON taller_linearepuesto (origen_repuesto)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS taller_linearepuesto_pieza_desarme_id_idx
                ON taller_linearepuesto (pieza_desarme_id)
                """
            )


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0099_empresa_is_trial_vehiculo_precio_compra"),
    ]

    operations = [
        migrations.RunPython(
            align_linearepuesto_desarme_columns,
            migrations.RunPython.noop,
        ),
    ]
