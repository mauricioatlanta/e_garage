from django.db import migrations, connection


def add_column_if_missing(apps, schema_editor):
    db_vendor = connection.vendor

    with connection.cursor() as cursor:
        if db_vendor == "postgresql":
            cursor.execute("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'taller_suscripciontransaccion'
                  AND column_name = 'legacy_pago_pendiente_id'
            """)
            exists = bool(cursor.fetchone())

            if not exists:
                cursor.execute("""
                    ALTER TABLE taller_suscripciontransaccion
                    ADD COLUMN legacy_pago_pendiente_id integer NULL
                    REFERENCES taller_pagopendiente(id)
                    ON DELETE SET NULL
                    DEFERRABLE INITIALLY DEFERRED
                """)

        elif db_vendor == "sqlite":
            cursor.execute(
                "PRAGMA table_info(taller_suscripciontransaccion)"
            )
            columns = [row[1] for row in cursor.fetchall()]

            if "legacy_pago_pendiente_id" not in columns:
                cursor.execute("""
                    ALTER TABLE taller_suscripciontransaccion
                    ADD COLUMN legacy_pago_pendiente_id integer NULL
                    REFERENCES taller_pagopendiente(id)
                """)


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0121_remove_clientetoken_cliente_delete_clientecredencial_and_more"),
    ]

    operations = [
        migrations.RunPython(
            add_column_if_missing,
            migrations.RunPython.noop,
        ),
    ]
