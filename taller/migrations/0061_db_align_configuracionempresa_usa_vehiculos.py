from django.db import migrations, connection


def add_usa_vehiculos_column(apps, schema_editor):
    """Agrega la columna usa_vehiculos si no existe"""
    with connection.cursor() as cursor:
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(taller_configuracionempresa)")
        columns = [row[1] for row in cursor.fetchall()]

        if "usa_vehiculos" not in columns:
            cursor.execute(
                """
                ALTER TABLE taller_configuracionempresa
                ADD COLUMN usa_vehiculos bool NOT NULL DEFAULT 0;
            """
            )


def reverse_migration(apps, schema_editor):
    """No revertimos - SQLite no soporta DROP COLUMN fácilmente"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0060_companysettings_whatsapp_template_notainterna_tipo"),
    ]

    operations = [
        migrations.RunPython(add_usa_vehiculos_column, reverse_migration),
    ]
