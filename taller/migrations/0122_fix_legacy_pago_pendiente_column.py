from django.db import migrations, connection


def add_column_if_missing(apps, schema_editor):
    db_vendor = connection.vendor
    if db_vendor == "postgresql":
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'taller_suscripciontransaccion'
                  AND column_name = 'legacy_pago_pendiente_id'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE taller_suscripciontransaccion
                    ADD COLUMN legacy_pago_pendiente_id integer NULL
                    REFERENCES taller_pagopendiente(id)
                    ON DELETE SET NULL
                    DEFERRABLE INITIALLY DEFERRED
                """)


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0121_remove_clientetoken_cliente_delete_clientecredencial_and_more"),
    ]

    operations = [
        migrations.RunPython(add_column_if_missing, migrations.RunPython.noop),
    ]
