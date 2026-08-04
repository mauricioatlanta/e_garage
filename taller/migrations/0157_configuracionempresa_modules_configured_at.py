from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0156_empresa_dominio"),
    ]

    operations = [
        migrations.AddField(
            model_name="configuracionempresa",
            name="modules_configured_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Módulos configurados el",
                help_text=(
                    "Fecha en que el usuario configuró explícitamente sus módulos de negocio. "
                    "Si es null, se mostrará el asistente de migración."
                ),
            ),
        ),
    ]
