from django.db import migrations, models
from django.utils.text import slugify


def generar_slugs(apps, schema_editor):
    Empresa = apps.get_model("taller", "Empresa")
    for empresa in Empresa.objects.order_by("pk"):
        base = slugify(empresa.nombre_taller)[:72] or "taller"
        candidato = base
        sufijo = 2
        while Empresa.objects.filter(slug=candidato).exclude(pk=empresa.pk).exists():
            candidato = f"{base}-{sufijo}"
            sufijo += 1
        empresa.slug = candidato
        empresa.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0132_kiosko_fase3_condicion"),
    ]

    operations = [
        # Paso 1: columna nullable para no romper filas existentes
        migrations.AddField(
            model_name="empresa",
            name="slug",
            field=models.SlugField(
                max_length=80,
                blank=True,
                null=True,
                help_text="Identificador URL de la tienda pública (/tienda/{slug})",
            ),
        ),
        # Paso 2: generar slugs para empresas ya existentes
        migrations.RunPython(generar_slugs, migrations.RunPython.noop),
        # Paso 3: ahora sí aplicar unique y NOT NULL
        migrations.AlterField(
            model_name="empresa",
            name="slug",
            field=models.SlugField(
                max_length=80,
                unique=True,
                blank=True,
                help_text="Identificador URL de la tienda pública (/tienda/{slug})",
            ),
        ),
    ]
