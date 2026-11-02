from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0068_db_align_configuracionempresa_usa_vehiculos"),
    ]

    # Compatibility no-op. The usa_servicios field is already introduced in
    # 0041_configuracionempresa_usa_kilometraje_and_more. This migration used
    # SQLite-only PRAGMA SQL and broke fresh PostgreSQL test databases.
    operations = []
