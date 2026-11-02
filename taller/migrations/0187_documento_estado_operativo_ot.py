from django.db import migrations, models
import django.utils.translation


def backfill_ot_estado_operativo(apps, schema_editor):
    Documento = apps.get_model("taller", "Documento")
    Documento.objects.filter(tipo="OT", estado_operativo_ot="").update(
        estado_operativo_ot="INGRESADO"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0186_public_analytics_hardening"),
    ]

    operations = [
        migrations.AddField(
            model_name="documento",
            name="estado_operativo_ot",
            field=models.CharField(
                blank=True,
                choices=[
                    ("INGRESADO", django.utils.translation.gettext_lazy("Vehículo Ingresado")),
                    ("DIAGNOSTICO", django.utils.translation.gettext_lazy("En Diagnóstico")),
                    (
                        "ESPERANDO_REPUESTOS",
                        django.utils.translation.gettext_lazy("Esperando Repuestos"),
                    ),
                    ("EN_REPARACION", django.utils.translation.gettext_lazy("En Reparación")),
                    ("LISTO", django.utils.translation.gettext_lazy("Listo para Entrega")),
                    ("ENTREGADO", django.utils.translation.gettext_lazy("Entregado")),
                ],
                db_index=True,
                default="",
                help_text=django.utils.translation.gettext_lazy(
                    "Estado operativo del taller para órdenes de trabajo."
                ),
                max_length=24,
            ),
        ),
        migrations.RunPython(backfill_ot_estado_operativo, migrations.RunPython.noop),
    ]
