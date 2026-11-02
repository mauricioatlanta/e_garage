# Generated migration for feature flag use_address_v2

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0028_catalogo_i18n_precios"),
    ]

    operations = [
        migrations.AddField(
            model_name="configuracionempresa",
            name="use_address_v2",
            field=models.BooleanField(
                default=False,
                help_text="Activar para usar el nuevo sistema de direcciones estructuradas (Address). Desactivar para seguir usando campos legacy (direccion, region, ciudad).",
                verbose_name="Usar Address v2",
            ),
        ),
    ]
