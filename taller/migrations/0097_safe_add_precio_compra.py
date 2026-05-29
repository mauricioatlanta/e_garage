from django.db import migrations


def add_precio_compra(apps, schema_editor):
    connection = schema_editor.connection
    cursor = connection.cursor()

    # Obtener columnas existentes
    if connection.vendor == "sqlite":
        cursor.execute("PRAGMA table_info(taller_vehiculo)")
        columns = [col[1] for col in cursor.fetchall()]
    else:
        cursor.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'taller_vehiculo'
        """
        )
        columns = [col[0] for col in cursor.fetchall()]

    # Si no existe precio_compra  crear
    if "precio_compra" not in columns:
        cursor.execute("ALTER TABLE taller_vehiculo ADD COLUMN precio_compra decimal")

    # Si existe costo_adquisicion  copiar datos
    if "costo_adquisicion" in columns:
        cursor.execute(
            """
            UPDATE taller_vehiculo
            SET precio_compra = costo_adquisicion
            WHERE precio_compra IS NULL
        """
        )


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0096_add_onboarding_fields_manual"),
    ]

    operations = [
        migrations.RunPython(add_precio_compra),
    ]
