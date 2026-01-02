# Generated manually to add missing CompanySettings fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0055_remove_logauditoria_empresa_and_more"),
    ]

    operations = [
        # Agregar campos faltantes de CompanySettings
        migrations.AddField(
            model_name="companysettings",
            name="terms_and_conditions",
            field=models.TextField(
                blank=True,
                help_text="Términos que aparecen en contratos y documentos",
                verbose_name="Términos y condiciones",
            ),
        ),
        migrations.AddField(
            model_name="companysettings",
            name="apply_tax_by_default",
            field=models.BooleanField(
                default=True,
                help_text="Aplicar impuesto automáticamente en nuevos documentos",
                verbose_name="Aplicar impuesto por defecto",
            ),
        ),
        migrations.AddField(
            model_name="companysettings",
            name="separate_by_technician",
            field=models.BooleanField(
                default=False,
                help_text="Mostrar reportes separados por técnico",
                verbose_name="Separar por técnico",
            ),
        ),
        migrations.AddField(
            model_name="companysettings",
            name="tax_rate",
            field=models.DecimalField(
                decimal_places=2,
                default=19.0,
                help_text="Tasa de impuesto por defecto (ej: 19.00 para Chile, 0.00 para USA)",
                max_digits=5,
                verbose_name="Tasa de impuesto",
            ),
        ),
    ]
