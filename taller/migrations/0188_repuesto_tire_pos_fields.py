from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0187_documento_estado_operativo_ot"),
    ]

    operations = [
        migrations.AddField(
            model_name="repuesto",
            name="codigo_oem",
            field=models.CharField(blank=True, db_index=True, max_length=64, null=True),
        ),
        migrations.AddField(
            model_name="repuesto",
            name="codigos_equivalentes",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Códigos alternativos separados por coma, espacio o salto de línea.",
            ),
        ),
        migrations.AddField(
            model_name="repuesto",
            name="ubicacion",
            field=models.CharField(
                blank=True,
                help_text="Ubicación física en bodega, estante o casillero.",
                max_length=120,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="repuesto",
            name="ancho",
            field=models.PositiveSmallIntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="repuesto",
            name="perfil",
            field=models.PositiveSmallIntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="repuesto",
            name="aro",
            field=models.PositiveSmallIntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="repuesto",
            name="indice_carga",
            field=models.CharField(blank=True, default="", max_length=10),
        ),
        migrations.AddField(
            model_name="repuesto",
            name="codigo_velocidad",
            field=models.CharField(blank=True, default="", max_length=5),
        ),
        migrations.AddField(
            model_name="repuesto",
            name="condicion",
            field=models.CharField(
                choices=[("nuevo", "Nuevo"), ("usado", "Usado")],
                db_index=True,
                default="nuevo",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="repuesto",
            name="profundidad_mm",
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True),
        ),
        migrations.AddField(
            model_name="repuesto",
            name="marca_neumatico",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="repuesto",
            name="modelo_neumatico",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddIndex(
            model_name="repuesto",
            index=models.Index(fields=["empresa", "codigo_oem"], name="taller_repu_empresa_24ec53_idx"),
        ),
        migrations.AddIndex(
            model_name="repuesto",
            index=models.Index(fields=["empresa", "ancho", "perfil", "aro"], name="taller_repu_empresa_ff6992_idx"),
        ),
    ]
