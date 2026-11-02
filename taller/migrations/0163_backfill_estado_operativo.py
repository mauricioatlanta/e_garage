"""
P2-DB Migración B — Backfill de estado_operativo.

Estrategia de inferencia (en orden de prioridad):
1. estado_desarme IN ('CERRADO', 'BAJA', 'AGOTADO') → CERRADO
2. Tiene PiezaDesarme                                → EN_PROCESAMIENTO
3. Tiene SugerenciaPiezaDesarme PENDIENTE/CONFIRMADA → EN_REVISION
4. Resto                                             → INGRESADO

Se crea un evento MIGRACION_ESTADO_INICIAL por vehículo para arrancar el
timeline desde P2. No se inventan fechas históricas — occurred_at = now().

Decisión: crear eventos en migración.
Razón: inicializa el timeline sin inventar datos históricos.
El evento MIGRACION_ESTADO_INICIAL es explícitamente distinguible.
"""

from django.db import migrations
from django.utils import timezone

# Estados legacy que representan cierre definitivo
_ESTADOS_CIERRE = {"CERRADO", "BAJA", "AGOTADO"}


def _backfill(apps, schema_editor):
    VehiculoDesarme     = apps.get_model("taller", "VehiculoDesarme")
    PiezaDesarme        = apps.get_model("taller", "PiezaDesarme")
    SugerenciaPiezaDesarme = apps.get_model("taller", "SugerenciaPiezaDesarme")
    VehiculoDesarmeEvent   = apps.get_model("taller", "VehiculoDesarmeEvent")

    now = timezone.now()

    # IDs por categoría — evita N+1 queries
    cerrados_ids = set(
        VehiculoDesarme.objects
        .filter(estado_desarme__in=list(_ESTADOS_CIERRE))
        .values_list("id", flat=True)
    )
    con_piezas_ids = set(
        PiezaDesarme.objects
        .exclude(vehiculo_desarme_id__in=cerrados_ids)
        .values_list("vehiculo_desarme_id", flat=True)
        .distinct()
    )
    con_sugerencias_ids = set(
        SugerenciaPiezaDesarme.objects
        .filter(estado__in=["PENDIENTE", "CONFIRMADA"])
        .exclude(vehiculo_desarme_id__in=cerrados_ids)
        .exclude(vehiculo_desarme_id__in=con_piezas_ids)
        .values_list("vehiculo_desarme_id", flat=True)
        .distinct()
    )

    def _resolver(vid):
        if vid in cerrados_ids:
            return "CERRADO"
        if vid in con_piezas_ids:
            return "EN_PROCESAMIENTO"
        if vid in con_sugerencias_ids:
            return "EN_REVISION"
        return "INGRESADO"

    # Actualizar y crear eventos en lotes
    eventos = []
    conteos = {"INGRESADO": 0, "EN_REVISION": 0, "EN_PROCESAMIENTO": 0, "CERRADO": 0}

    for v in VehiculoDesarme.objects.select_related("empresa"):
        nuevo = _resolver(v.id)
        VehiculoDesarme.objects.filter(pk=v.pk).update(estado_operativo=nuevo)
        conteos[nuevo] = conteos.get(nuevo, 0) + 1
        eventos.append(
            VehiculoDesarmeEvent(
                empresa=v.empresa,
                vehiculo=v,
                tipo="MIGRACION_ESTADO_INICIAL",
                occurred_at=now,
                metadata={
                    "source": "migration",
                    "inferred": True,
                    "to": nuevo,
                    "estado_desarme_legacy": v.estado_desarme or "",
                },
            )
        )

    VehiculoDesarmeEvent.objects.bulk_create(eventos, batch_size=500)

    total = sum(conteos.values())
    print(
        f"\n  [backfill] VehiculoDesarme: {total} procesados — "
        f"INGRESADO={conteos['INGRESADO']}, "
        f"EN_REVISION={conteos['EN_REVISION']}, "
        f"EN_PROCESAMIENTO={conteos['EN_PROCESAMIENTO']}, "
        f"CERRADO={conteos['CERRADO']}"
    )
    print(f"  [backfill] Eventos MIGRACION_ESTADO_INICIAL creados: {len(eventos)}")


def _revert(apps, schema_editor):
    VehiculoDesarme = apps.get_model("taller", "VehiculoDesarme")
    VehiculoDesarmeEvent = apps.get_model("taller", "VehiculoDesarmeEvent")
    # Revertir a INGRESADO (safe default)
    VehiculoDesarme.objects.update(estado_operativo="INGRESADO")
    VehiculoDesarmeEvent.objects.filter(tipo="MIGRACION_ESTADO_INICIAL").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("taller", "0162_vehiculodesarme_estado_operativo_events"),
    ]

    operations = [
        migrations.RunPython(_backfill, _revert),
    ]
