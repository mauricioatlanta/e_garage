from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0061_db_align_configuracionempresa_usa_vehiculos"),
        ("taller", "0069_db_align_configuracionempresa_usa_servicios"),
    ]

    # Compatibility no-op. The giro field is already introduced in
    # 0057_agregar_campo_giro_cliente. This hotfix used SQLite-only PRAGMA SQL
    # and broke fresh PostgreSQL test databases.
    operations = []
