from django.db import migrations, connection


def add_giro_column(apps, schema_editor):
    """Agrega la columna giro si no existe"""
    with connection.cursor() as cursor:
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(taller_cliente)")
        columns = [row[1] for row in cursor.fetchall()]

        if "giro" not in columns:
            cursor.execute(
                """
                ALTER TABLE taller_cliente
                ADD COLUMN giro TEXT NULL;
            """
            )


def reverse_migration(apps, schema_editor):
    """No revertimos"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0061_db_align_configuracionempresa_usa_vehiculos"),
        ("taller", "0069_db_align_configuracionempresa_usa_servicios"),
    ]

    operations = [
        migrations.RunPython(add_giro_column, reverse_migration),
    ]
