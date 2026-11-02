from django.db import migrations
from django.db.models import Q
from django.utils.text import slugify


def backfill_slugs(apps, schema_editor):
    """
    Genera slug para cada Empresa que no lo tiene, usando la misma lógica
    que Empresa._generar_slug_unico() en el modelo actual.

    La lógica se replica inline porque el modelo histórico de la migración
    no expone métodos de instancia del modelo real.
    """
    Empresa = apps.get_model("taller", "Empresa")
    sin_slug = Empresa.objects.filter(Q(slug__isnull=True) | Q(slug=""))

    for empresa in sin_slug.order_by("id"):
        base = slugify(empresa.nombre_taller)[:72] or "taller"
        candidato = base
        sufijo = 2
        qs = Empresa.objects.exclude(pk=empresa.pk)
        while qs.filter(slug=candidato).exists():
            candidato = f"{base}-{sufijo}"
            sufijo += 1
        empresa.slug = candidato
        empresa.save(update_fields=["slug"])


def reverse_backfill_slugs(apps, schema_editor):
    # No-op intencional.
    #
    # No es posible distinguir de forma fiable qué slugs existían antes de
    # esta migración y cuáles fueron generados por ella, sin almacenar estado
    # adicional. Revertir sobrescribiría slugs que podrían ya estar en uso
    # en URLs de producción.
    #
    # Si se necesita limpiar slugs generados por esta migración, hacerlo con
    # una migración de datos ad-hoc apuntando a los IDs específicos.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0148_empresa_marcas_permitidas_catalogo"),
    ]

    operations = [
        migrations.RunPython(backfill_slugs, reverse_backfill_slugs),
    ]
