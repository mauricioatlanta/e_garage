import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("taller", "0101_repuesto_stock_minimo"),
    ]

    operations = [
        migrations.AddField(
            model_name="documento",
            name="approved_at",
            field=models.DateTimeField(
                blank=True,
                db_index=True,
                help_text="Fecha y hora en que el cliente aprobo el presupuesto",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="documento",
            name="approved_by",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Nombre del cliente que aprobo el presupuesto",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="documento",
            name="approved_ip",
            field=models.GenericIPAddressField(
                blank=True,
                help_text="Direccion IP desde la cual se aprobo el presupuesto",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="documento",
            name="uuid",
            field=models.UUIDField(
                db_index=True,
                default=uuid.uuid4,
                editable=False,
                unique=True,
            ),
        ),
    ]
