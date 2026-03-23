# Correlativo por empresa y tipo (recibo / invoice) para numeración PRO

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0088_pieza_desarme_name_canonico_i18n"),
    ]

    operations = [
        migrations.CreateModel(
            name="CorrelativoDocumento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tipo", models.CharField(db_index=True, max_length=20)),
                ("ultimo_numero", models.PositiveIntegerField(default=0)),
                (
                    "empresa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="correlativos_documento",
                        to="taller.empresa",
                    ),
                ),
            ],
            options={
                "verbose_name": "Correlativo de documento",
                "verbose_name_plural": "Correlativos de documentos",
            },
        ),
        migrations.AddConstraint(
            model_name="correlativodocumento",
            constraint=models.UniqueConstraint(fields=("empresa", "tipo"), name="taller_correlativodoc_empresa_tipo_uniq"),
        ),
    ]
