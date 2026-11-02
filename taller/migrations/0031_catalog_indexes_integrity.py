# Generated migration for catalog indexes and integrity constraints

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0030_normalize_ubicaciones"),
    ]

    operations = [
        # ============================================================================
        # PART: Agregar db_index a SKU
        # ============================================================================
        migrations.AlterField(
            model_name="part",
            name="sku",
            field=models.CharField(
                db_index=True,
                help_text="Código único del repuesto (SKU/Part Number)",
                max_length=64,
                unique=True,
                verbose_name="SKU",
            ),
        ),
        # ============================================================================
        # SERVICE: Agregar db_index a code
        # ============================================================================
        migrations.AlterField(
            model_name="service",
            name="code",
            field=models.CharField(
                db_index=True,
                help_text="Código único del servicio (ej: OIL_CHANGE, BRAKE_SERVICE)",
                max_length=64,
                unique=True,
                verbose_name="Código",
            ),
        ),
        # ============================================================================
        # TAXPOLICY: Índices compuestos
        # ============================================================================
        # Agregar nuevos índices optimizados
        migrations.AddIndex(
            model_name="taxpolicy",
            index=models.Index(
                fields=["country", "state_code", "city_name", "applies_to", "active"],
                name="idx_taxpolicy_lookup",
            ),
        ),
        migrations.AddIndex(
            model_name="taxpolicy",
            index=models.Index(fields=["country", "active"], name="idx_taxpolicy_country"),
        ),
        migrations.AddIndex(
            model_name="taxpolicy",
            index=models.Index(fields=["country", "state_code"], name="idx_taxpolicy_state"),
        ),
        # ============================================================================
        # PARTPRICE: Índices compuestos
        # ============================================================================
        # Agregar nuevos índices optimizados
        migrations.AddIndex(
            model_name="partprice",
            index=models.Index(
                fields=["company", "part", "valid_from", "valid_to"], name="idx_partprice_lookup"
            ),
        ),
        migrations.AddIndex(
            model_name="partprice",
            index=models.Index(fields=["part", "valid_from"], name="idx_partprice_part"),
        ),
        migrations.AddIndex(
            model_name="partprice",
            index=models.Index(fields=["company", "valid_from"], name="idx_partprice_company"),
        ),
        # ============================================================================
        # SERVICEPRICE: Índices compuestos
        # ============================================================================
        # Agregar nuevos índices optimizados
        migrations.AddIndex(
            model_name="serviceprice",
            index=models.Index(
                fields=["company", "service", "valid_from", "valid_to"],
                name="idx_serviceprice_lookup",
            ),
        ),
        migrations.AddIndex(
            model_name="serviceprice",
            index=models.Index(fields=["service", "valid_from"], name="idx_serviceprice_service"),
        ),
        migrations.AddIndex(
            model_name="serviceprice",
            index=models.Index(fields=["company", "valid_from"], name="idx_serviceprice_company"),
        ),
    ]
