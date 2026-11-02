from django.db import migrations, models


def backfill_publicada(apps, schema_editor):
    """Piezas activas y disponibles se publican automáticamente — conservan visibilidad previa."""
    PiezaDesarme = apps.get_model("taller", "PiezaDesarme")
    PiezaDesarme.objects.filter(
        activo=True,
        estado_pieza="DISPONIBLE",
    ).update(publicada=True)


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0160_trust_sesion_usuario"),
    ]

    operations = [
        migrations.AddField(
            model_name="piezadesarme",
            name="publicada",
            field=models.BooleanField(
                default=False,
                db_index=True,
                help_text=(
                    "Compuerta del kiosko. True = visible en storefront y kiosko. "
                    "False = en proceso (confirmada pero no publicada aún)."
                ),
            ),
        ),
        migrations.AddIndex(
            model_name="piezadesarme",
            index=models.Index(
                fields=["empresa", "publicada", "estado_pieza"],
                name="taller_piez_empresa_pub_estado_idx",
            ),
        ),
        migrations.RunPython(backfill_publicada, migrations.RunPython.noop),
    ]
