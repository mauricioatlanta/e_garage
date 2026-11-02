# Fase B: Data migration Vehiculo(tipo_uso=DESARME) -> VehiculoDesarme

import logging

from django.db import migrations

logger = logging.getLogger(__name__)


def forwards(apps, schema_editor):
    Vehiculo = apps.get_model("taller", "Vehiculo")
    VehiculoDesarme = apps.get_model("taller", "VehiculoDesarme")
    qs = Vehiculo.objects.filter(tipo_uso="DESARME")
    total_leidos = qs.count()
    total_creados = 0
    total_existentes = 0
    total_warnings = 0
    ids_warnings = []

    for v in qs.iterator():
        if VehiculoDesarme.objects.filter(vehiculo_origen_id=v.id).exists():
            total_existentes += 1
            continue

        patente_ok = v.patente and str(v.patente).strip()
        vin_ok = v.vin and str(v.vin).strip()
        if not (patente_ok or vin_ok):
            total_warnings += 1
            ids_warnings.append(v.id)

        vd = VehiculoDesarme(
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
            costo_adquisicion=v.costo_adquisicion,
            fecha_ingreso_desarme=v.fecha_ingreso_desarme,
            estado_desarme=v.estado_desarme,
            ubicacion_fisica=v.ubicacion_fisica,
            fecha_baja_desarme=v.fecha_baja_desarme,
            observaciones_desarme=v.observaciones_desarme,
        )
        vd.save()
        total_creados += 1

    logger.info(
        "Desarme migration: leidos=%s creados=%s existentes=%s warnings=%s ids_warnings=%s",
        total_leidos,
        total_creados,
        total_existentes,
        total_warnings,
        ids_warnings[:100] if ids_warnings else [],
    )


def backwards(apps, schema_editor):
    """Borrar solo los VehiculoDesarme que vinieron de migración (vehiculo_origen_id not null)."""
    VehiculoDesarme = apps.get_model("taller", "VehiculoDesarme")
    VehiculoDesarme.objects.filter(vehiculo_origen_id__isnull=False).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0077_vehiculodesarme"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
