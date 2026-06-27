import logging

from django.db import migrations

logger = logging.getLogger(__name__)


def forwards(apps, schema_editor):
    Vehiculo = apps.get_model("taller", "Vehiculo")
    VehiculoDesarme = apps.get_model("taller", "VehiculoDesarme")

    # ── Paso 1: Top-up sync ────────────────────────────────────────────────
    # Crea VehiculoDesarme para cualquier Vehiculo(DESARME) que haya entrado
    # entre que 0141 se aplicó y ahora. Misma lógica de 0141; es idempotente.
    nuevos = 0
    for v in Vehiculo.objects.filter(tipo_uso="DESARME").order_by("id").iterator():
        if VehiculoDesarme.objects.filter(vehiculo_origen_id=v.id).exists():
            continue
        vd = VehiculoDesarme(
            id=v.id,
            empresa_id=v.empresa_id,
            vehiculo_origen_id=v.id,
            marca_id=v.marca_id,
            marca_texto=v.marca_texto,
            modelo_id=v.modelo_id,
            modelo_texto=v.modelo_texto,
            patente=v.patente or "",
            anio=v.anio,
            color_id=v.color_id,
            vin=v.vin,
            motor_id=v.motor_id,
            caja_id=v.caja_id,
            millas=v.millas,
            fecha_ingreso_desarme=v.fecha_ingreso_desarme,
            estado_desarme=v.estado_desarme,
            ubicacion_fisica=v.ubicacion_fisica,
            fecha_baja_desarme=v.fecha_baja_desarme,
            observaciones_desarme=v.observaciones_desarme,
            es_placeholder=bool(v.es_placeholder),
            tipo_carroceria=v.tipo_carroceria,
            precio_compra=v.precio_compra,
            monto_chatarra=v.monto_chatarra,
            transporte_grua_desarme=v.transporte_grua_desarme,
            otros_gastos_desarme=v.otros_gastos_desarme,
            vendedor_desarme_id=v.vendedor_desarme_id,
        )
        vd.save(force_insert=True)
        nuevos += 1

    if nuevos > 0 and schema_editor.connection.vendor == "postgresql":
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                "SELECT setval("
                "    pg_get_serial_sequence('taller_vehiculodesarme', 'id'),"
                "    COALESCE((SELECT MAX(id) FROM taller_vehiculodesarme), 1)"
                ")"
            )
    logger.info("0143 top-up sync: %s nuevos VehiculoDesarme creados", nuevos)

    # ── Paso 2: UPDATEs directos ──────────────────────────────────────────
    # vehiculo_desarme_id = vehiculo_id es válido porque 0141 + top-up sync
    # garantizan que cada vehiculo_id tiene VehiculoDesarme.id idéntico.
    tablas = [
        "taller_piezadesarme",
        "taller_sugerenciapiezadesarme",
        "taller_preciohistoricopieza",
        "taller_vehiculofinancialsnapshot",
        "taller_vehiclefinancialevent",
    ]
    with schema_editor.connection.cursor() as cursor:
        for tabla in tablas:
            cursor.execute(
                f"UPDATE {tabla} SET vehiculo_desarme_id = vehiculo_id"
                f" WHERE vehiculo_desarme_id IS NULL"
            )

    # ── Paso 3: Validación — aborta si queda algún NULL ───────────────────
    with schema_editor.connection.cursor() as cursor:
        for tabla in tablas:
            cursor.execute(
                f"SELECT COUNT(*) FROM {tabla} WHERE vehiculo_desarme_id IS NULL"
            )
            count = cursor.fetchone()[0]
            if count > 0:
                raise ValueError(
                    f"0143 abortado: {tabla} tiene {count} filas con "
                    f"vehiculo_desarme_id NULL tras el UPDATE. "
                    f"Revisar si hay vehiculo_id sin VehiculoDesarme correspondiente."
                )

    logger.info("0143: vehiculo_desarme_id poblado en %s tablas", len(tablas))


def backwards(apps, schema_editor):
    tablas = [
        "taller_piezadesarme",
        "taller_sugerenciapiezadesarme",
        "taller_preciohistoricopieza",
        "taller_vehiculofinancialsnapshot",
        "taller_vehiclefinancialevent",
    ]
    with schema_editor.connection.cursor() as cursor:
        for tabla in tablas:
            cursor.execute(f"UPDATE {tabla} SET vehiculo_desarme_id = NULL")


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0142_fase2_add_vehiculo_desarme_nullable"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
