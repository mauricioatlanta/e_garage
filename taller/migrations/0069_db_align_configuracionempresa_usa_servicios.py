from django.db import migrations, connection

def add_usa_servicios_column(apps, schema_editor):
    """Agrega la columna usa_servicios si no existe"""
    with connection.cursor() as cursor:
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(taller_configuracionempresa)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'usa_servicios' not in columns:
            cursor.execute("""
                ALTER TABLE taller_configuracionempresa
                ADD COLUMN usa_servicios INTEGER NOT NULL DEFAULT 0;
            """)

def reverse_migration(apps, schema_editor):
    """No revertimos - la columna puede ser necesaria"""
    pass

class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0068_db_align_configuracionempresa_usa_vehiculos"),
    ]

    operations = [
        migrations.RunPython(add_usa_servicios_column, reverse_migration),
    ]
