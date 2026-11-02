# Recreated migration file (was applied in DB but missing from repo after cleanup)
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0073_logauditoria_marcavehiculo_modelovehiculo_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ChecklistIngreso",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nivel_combustible", models.PositiveIntegerField()),
                ("luces_funcionan", models.BooleanField(default=False)),
                ("objetos_valor", models.TextField(default="", blank=True)),
                ("danos", models.TextField(default="", blank=True)),
                ("fotos_4_angulos", models.TextField(default="", blank=True)),
                ("foto_frontal", models.ImageField(upload_to="ingreso/", blank=True, null=True, max_length=100)),
                ("foto_trasera", models.ImageField(upload_to="ingreso/", blank=True, null=True, max_length=100)),
                ("foto_lateral_1", models.ImageField(upload_to="ingreso/", blank=True, null=True, max_length=100)),
                ("foto_lateral_2", models.ImageField(upload_to="ingreso/", blank=True, null=True, max_length=100)),
                (
                    "documento",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="checklist_ingreso",
                        to="taller.documento",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="RegistroKilometraje",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kilometraje", models.PositiveIntegerField()),
                ("fecha", models.DateTimeField()),
                ("foto_tablero", models.ImageField(upload_to="ingreso/", blank=True, null=True, max_length=100)),
                ("omitido_motivo", models.CharField(max_length=255, default="", blank=True)),
                ("source", models.CharField(max_length=20, default="manual")),
                (
                    "created_by",
                    models.ForeignKey(
                        to=settings.AUTH_USER_MODEL,
                        null=True,
                        blank=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                    ),
                ),
                ("empresa", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="taller.empresa")),
                ("vehiculo", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="taller.vehiculo")),
            ],
        ),
    ]
