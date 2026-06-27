# Data migration: copia Vehiculo(tipo_uso='DESARME') → VehiculoDesarme.
#
# Por qué IDs explícitos: PiezaDesarme.vehiculo_id apunta a taller_vehiculo.id.
# Preservar esos IDs en VehiculoDesarme permite que la Fase 4 (repunte de FK)
# sea un simple UPDATE de columna en lugar de un mapeo ID-a-ID.
#
# created_at / updated_at quedan con la fecha de esta migración (auto_now_add).
# No se intenta preservar los timestamps originales de Vehiculo.

import logging

from django.db import migrations

logger = logging.getLogger(__name__)


def forwards(apps, schema_editor):
    Vehiculo = apps.get_model("taller", "Vehiculo")
    VehiculoDesarme = apps.get_model("taller", "VehiculoDesarme")

    qs = Vehiculo.objects.filter(tipo_uso="DESARME").order_by("id")
    total = qs.count()
    creados = 0
    saltados = 0
    sin_identificador = []

    for v in qs.iterator():
        # Idempotencia: si ya existe una fila con vehiculo_origen_id=v.id, saltarla.
        # Cubre reintento tras fallo parcial sin duplicar datos.
        if VehiculoDesarme.objects.filter(vehiculo_origen_id=v.id).exists():
            saltados += 1
            continue

        tiene_patente = bool(v.patente and str(v.patente).strip())
        tiene_vin = bool(v.vin and str(v.vin).strip())
        if not (tiene_patente or tiene_vin):
            sin_identificador.append(v.id)

        vd = VehiculoDesarme(
            # PK explícita para paridad con los FK de PiezaDesarme.
            id=v.id,
            empresa_id=v.empresa_id,
            vehiculo_origen_id=v.id,
            # Identificación del vehículo
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
            # Campos de desarme copiados por la vieja 0078
            fecha_ingreso_desarme=v.fecha_ingreso_desarme,
            estado_desarme=v.estado_desarme,
            ubicacion_fisica=v.ubicacion_fisica,
            fecha_baja_desarme=v.fecha_baja_desarme,
            observaciones_desarme=v.observaciones_desarme,
            # Campos que 0078 omitió — todos asignados explícitamente.
            # es_placeholder no tiene default a nivel DB (BooleanField default=False
            # en el modelo Python, pero la columna DB admite cualquier bool).
            # Se asigna con bool() para que nunca llegue None.
            es_placeholder=bool(v.es_placeholder),
            tipo_carroceria=v.tipo_carroceria,
            precio_compra=v.precio_compra,
            monto_chatarra=v.monto_chatarra,
            transporte_grua_desarme=v.transporte_grua_desarme,
            otros_gastos_desarme=v.otros_gastos_desarme,
            vendedor_desarme_id=v.vendedor_desarme_id,
        )
        # force_insert=True garantiza INSERT aunque id esté explícito.
        # Sin esto, Django podría intentar UPDATE si detecta pk set.
        vd.save(force_insert=True)
        creados += 1

    logger.info(
        "0141 forwards: total=%s creados=%s saltados=%s "
        "sin_identificador=%s ids=%s",
        total,
        creados,
        saltados,
        len(sin_identificador),
        sin_identificador[:50] if sin_identificador else [],
    )

    # Avanzar la secuencia Postgres para que el próximo INSERT con id autogenerado
    # no colisione con los IDs explícitos recién insertados.
    # Nota: setval() es no-transaccional en Postgres — persiste aunque el
    # bloque surrounding haga rollback. Eso es correcto: una secuencia
    # adelantada es inofensiva; una secuencia detrás de MAX(id) causaría error.
    if schema_editor.connection.vendor == "postgresql":
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                "SELECT setval("
                "    pg_get_serial_sequence('taller_vehiculodesarme', 'id'),"
                "    COALESCE((SELECT MAX(id) FROM taller_vehiculodesarme), 1)"
                ")"
            )
        logger.info("0141: secuencia taller_vehiculodesarme reseteada")


def backwards(apps, schema_editor):
    """Borra solo las filas que vinieron de esta migración (vehiculo_origen_id IS NOT NULL).
    Las filas creadas manualmente después de la migración (vehiculo_origen_id NULL)
    no se tocan.
    """
    VehiculoDesarme = apps.get_model("taller", "VehiculoDesarme")
    deleted, _ = VehiculoDesarme.objects.filter(vehiculo_origen_id__isnull=False).delete()
    logger.info("0141 backwards: eliminadas %s filas de VehiculoDesarme", deleted)

    if schema_editor.connection.vendor == "postgresql":
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                "SELECT setval("
                "    pg_get_serial_sequence('taller_vehiculodesarme', 'id'),"
                "    COALESCE((SELECT MAX(id) FROM taller_vehiculodesarme), 1)"
                ")"
            )


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0140_vehiculodesarme_campos_paridad"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
