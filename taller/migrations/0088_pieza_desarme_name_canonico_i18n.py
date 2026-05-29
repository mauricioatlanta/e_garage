# Fase 2: modelo canónico i18n/aliases para piezas de desarme

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0087_pieza_desarme_valorizacion_v4_precio_historico"),
    ]

    operations = [
        migrations.CreateModel(
            name="PiezaDesarmeName",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "language",
                    models.CharField(
                        choices=[("es", "Español"), ("en", "English"), ("pt", "Português")],
                        max_length=2,
                    ),
                ),
                (
                    "label",
                    models.CharField(help_text="Nombre canónico en este idioma", max_length=255),
                ),
                (
                    "aliases",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="Lista de sinónimos/slang para búsqueda (ej. ['engine', 'motor'])",
                    ),
                ),
                (
                    "is_default",
                    models.BooleanField(
                        default=False,
                        help_text="Nombre principal para este idioma (un solo True por pieza+language)",
                    ),
                ),
                (
                    "pieza_desarme",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="names",
                        to="taller.piezadesarme",
                    ),
                ),
            ],
            options={
                "verbose_name": "Nombre de pieza desarme",
                "verbose_name_plural": "Nombres de piezas desarme",
            },
        ),
        migrations.AddConstraint(
            model_name="piezadesarmename",
            constraint=models.UniqueConstraint(
                fields=("pieza_desarme", "language", "is_default"),
                name="uq_pieza_desarme_name_pieza_lang_default",
            ),
        ),
    ]
