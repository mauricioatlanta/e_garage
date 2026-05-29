from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0060_companysettings_whatsapp_template_notainterna_tipo"),
    ]

    # Compatibility no-op. The usa_vehiculos field is already introduced in
    # 0041_configuracionempresa_usa_kilometraje_and_more. This migration used
    # SQLite-only PRAGMA SQL and broke fresh PostgreSQL test databases.
    operations = []
