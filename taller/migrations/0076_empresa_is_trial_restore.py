# Restaura el campo is_trial en Empresa tras haber sido eliminado en 0073.
# El modelo Empresa lo define; la migración 0073 lo quitó del estado y de la BD.
# Esta migración lo vuelve a crear para que esquema y modelo coincidan.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0075_vehiculo_tipo_uso_desarme"),
    ]

    operations = [
        migrations.AddField(
            model_name="empresa",
            name="is_trial",
            field=models.BooleanField(
                default=False,
                help_text="Indica si la empresa está actualmente en período de prueba",
                null=True,
            ),
        ),
    ]
