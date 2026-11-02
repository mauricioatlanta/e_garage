# Generated for Fase 3 — tipo_carroceria formal choices + max_length=20
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0136_unique_codigo_por_empresa_vehiculo"),
    ]

    operations = [
        migrations.AlterField(
            model_name="vehiculo",
            name="tipo_carroceria",
            field=models.CharField(
                blank=True,
                choices=[
                    ("sedan", "Sedán"),
                    ("suv", "SUV"),
                    ("pickup", "Pickup"),
                    ("hatchback", "Hatchback"),
                    ("coupe", "Coupé"),
                    ("station_wagon", "Station Wagon"),
                    ("van", "Van"),
                    ("minivan", "Minivan"),
                    ("convertible", "Convertible"),
                    ("crossover", "Crossover"),
                    ("compacto", "Compacto"),
                    ("utilitario", "Utilitario"),
                    ("camion", "Camión"),
                    ("moto", "Motocicleta"),
                    ("otro", "Otro"),
                ],
                max_length=20,
                null=True,
                verbose_name="Tipo de carrocería",
            ),
        ),
    ]
