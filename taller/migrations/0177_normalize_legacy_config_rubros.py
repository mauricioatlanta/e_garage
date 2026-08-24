from django.db import migrations


ALIASES = {
    "DESARME": "DESARMADURIA",
    "REPUESTOS": "PARTS",
    "CASA_REPUESTOS": "PARTS",
}


def forwards(apps, schema_editor):
    ConfiguracionEmpresa = apps.get_model("taller", "ConfiguracionEmpresa")

    for config in ConfiguracionEmpresa.objects.all().iterator():
        raw = list(config.rubros or [])
        normalized = [ALIASES.get(value, value) for value in raw]

        if normalized != raw:
            config.rubros = normalized
            config.save(update_fields=["rubros"])


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0176_country_service_rubro_catalog"),
    ]

    operations = [
        migrations.RunPython(
            forwards,
            backwards,
        ),
    ]
