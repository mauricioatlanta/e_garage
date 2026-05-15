# Generated migration for ubicaciones normalization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0029_add_use_address_v2_flag"),
    ]

    operations = [
        # 1. Modificar Estado.codigo (aumentar max_length a 10)
        migrations.AlterField(
            model_name="estado",
            name="codigo",
            field=models.CharField(
                help_text="Código del estado (GA, SP, RM, LIM, etc.) - Único por país",
                max_length=10,
                verbose_name="Código",
            ),
        ),
        # 2. Modificar Estado.pais (remover default, agregar help_text)
        migrations.AlterField(
            model_name="estado",
            name="pais",
            field=models.CharField(
                choices=[
                    ("CL", "Chile"),
                    ("US", "Estados Unidos"),
                    ("BR", "Brasil"),
                    ("PE", "Perú"),
                    ("VE", "Venezuela"),
                ],
                help_text="Código de país ISO 3166-1 alpha-2",
                max_length=2,
                verbose_name="País",
            ),
        ),
        # 3. Agregar índice en Estado: (pais, codigo)
        migrations.AddIndex(
            model_name="estado",
            index=models.Index(fields=["pais", "codigo"], name="idx_estado_pais_codigo"),
        ),
        # 4. Agregar índice en Estado: (pais)
        migrations.AddIndex(
            model_name="estado",
            index=models.Index(fields=["pais"], name="idx_estado_pais"),
        ),
        # 5. Modificar Ciudad.estado (cambiar a string reference)
        migrations.AlterField(
            model_name="ciudad",
            name="estado",
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name="ciudades",
                to="taller.estado",  # ✅ String reference (lowercase en migración)
            ),
        ),
        # 6. Agregar índice en Ciudad: (estado, nombre)
        migrations.AddIndex(
            model_name="ciudad",
            index=models.Index(fields=["estado", "nombre"], name="idx_ciudad_estado_nombre"),
        ),
        # 7. Agregar índice en Ciudad: (estado)
        migrations.AddIndex(
            model_name="ciudad",
            index=models.Index(fields=["estado"], name="idx_ciudad_estado"),
        ),
    ]
