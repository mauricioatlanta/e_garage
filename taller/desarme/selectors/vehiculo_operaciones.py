"""
Selector de lectura pura para el Centro de Operaciones de un vehículo de desarme.

Contrato: get_vehicle_operations_summary(*, empresa, vehiculo, user=None, request=None)
  - Sin efectos secundarios.
  - Sin escrituras.
  - Retorna un dict estructurado listo para el template.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.db.models import Sum, F
from django.utils import timezone
from django.utils.translation import gettext as _

from taller.models.pieza_desarme import (
    ESTADO_DISPONIBLE,
    ESTADO_VENDIDA,
    ESTADO_DANADA,
    ESTADO_FALTANTE,
    ESTADO_SCRAP,
    PiezaDesarme,
)
from taller.models.lineas_documento import LineaRepuesto, ORIGEN_DESARME
from taller.models.sugerencia_pieza_desarme import SugerenciaPiezaDesarme
from taller.models.vehiculo_desarme import EstadoOperativo
from taller.models.vehiculo_desarme_event import VehiculoDesarmeEvent, TipoEventoDesarme


_PROGRESS_BY_STATE = {
    EstadoOperativo.INGRESADO:        10,
    EstadoOperativo.EN_REVISION:      30,
    EstadoOperativo.EN_PROCESAMIENTO: 60,
    EstadoOperativo.EN_CIERRE:        85,
    EstadoOperativo.CERRADO:         100,
}

_STATE_LABEL = {
    EstadoOperativo.INGRESADO:        "Ingresado",
    EstadoOperativo.EN_REVISION:      "En revisión",
    EstadoOperativo.EN_PROCESAMIENTO: "En procesamiento",
    EstadoOperativo.EN_CIERRE:        "En cierre",
    EstadoOperativo.CERRADO:          "Cerrado",
}

_STATE_TONE = {
    EstadoOperativo.INGRESADO:        "slate",
    EstadoOperativo.EN_REVISION:      "amber",
    EstadoOperativo.EN_PROCESAMIENTO: "cyan",
    EstadoOperativo.EN_CIERRE:        "blue",
    EstadoOperativo.CERRADO:          "emerald",
}

_STALE_DAYS = 30
_NO_SALES_WARNING_DAYS = 14


def _build_url(request, suffix: str) -> str:
    """Builds a desarme URL from request context. Falls back to CL path."""
    if request is None:
        return f"/cl/es/desarme/{suffix}"
    path = (request.path or "").strip("/")
    if path.startswith("us/"):
        base = "/us/en"
    else:
        base = "/cl/es"
    return f"{base}/desarme/{suffix.lstrip('/')}"


def get_vehicle_operations_summary(
    *,
    empresa,
    vehiculo,
    user=None,
    request=None,
) -> dict[str, Any]:
    """
    Returns a structured dict describing the operational state of a salvage vehicle.
    Pure read: no side effects, no writes.
    """
    now = timezone.now()
    estado = vehiculo.estado_operativo or EstadoOperativo.INGRESADO

    # ── Piezas ─────────────────────────────────────────────────────────────────
    piezas_qs = PiezaDesarme.objects.filter(
        empresa=empresa,
        vehiculo_desarme=vehiculo,
        activo=True,
    )
    piezas = list(piezas_qs.values(
        "id", "estado_pieza", "publicada", "precio_venta_sugerido", "cantidad",
    ))

    disponibles = [p for p in piezas if p["estado_pieza"] == ESTADO_DISPONIBLE]
    vendidas_count = piezas_qs.filter(estado_pieza=ESTADO_VENDIDA).count()
    danadas_count = sum(1 for p in piezas if p["estado_pieza"] == ESTADO_DANADA)
    faltantes_count = sum(1 for p in piezas if p["estado_pieza"] == ESTADO_FALTANTE)

    publicadas = [p for p in disponibles if p["publicada"]]
    sin_publicar = [p for p in disponibles if not p["publicada"]]
    sin_precio = [
        p for p in disponibles
        if not p["precio_venta_sugerido"] or p["precio_venta_sugerido"] == Decimal("0")
    ]

    total_piezas = len(piezas) + vendidas_count

    # ── Sugerencias de revisión ────────────────────────────────────────────────
    sugerencias_qs = SugerenciaPiezaDesarme.objects.filter(
        empresa=empresa,
        vehiculo_desarme=vehiculo,
    )
    sug_pendientes = sugerencias_qs.filter(estado=SugerenciaPiezaDesarme.PENDIENTE).count()
    sug_confirmadas = sugerencias_qs.filter(estado=SugerenciaPiezaDesarme.CONFIRMADA).count()
    sug_descartadas = sugerencias_qs.filter(estado=SugerenciaPiezaDesarme.DESCARTADA).count()
    sug_total = sug_pendientes + sug_confirmadas + sug_descartadas

    # ── Financiero ─────────────────────────────────────────────────────────────
    costo_compra = vehiculo.precio_compra or Decimal("0")
    costo_transporte = vehiculo.transporte_grua_desarme or Decimal("0")
    costo_otros = vehiculo.otros_gastos_desarme or Decimal("0")
    costo_total = costo_compra + costo_transporte + costo_otros

    total_recaudado = (
        LineaRepuesto.objects.filter(
            origen_repuesto=ORIGEN_DESARME,
            pieza_desarme__vehiculo_desarme=vehiculo,
        ).aggregate(total=Sum(F("precio_unitario") * F("cantidad")))["total"]
        or Decimal("0")
    )

    valor_potencial = sum(
        (p["precio_venta_sugerido"] or Decimal("0")) * p["cantidad"]
        for p in disponibles
    )

    pct_recuperado: float = 0.0
    if costo_total > 0:
        pct_recuperado = float(total_recaudado / costo_total * 100)

    # ── Tiempo en estado actual ────────────────────────────────────────────────
    last_state_change = (
        VehiculoDesarmeEvent.objects.filter(
            empresa=empresa,
            vehiculo=vehiculo,
            tipo=TipoEventoDesarme.ESTADO_OPERATIVO_CAMBIADO,
        )
        .order_by("-occurred_at")
        .values_list("occurred_at", flat=True)
        .first()
    )
    if last_state_change:
        dias_en_estado = (now - last_state_change).days
    else:
        dias_en_estado = (now - vehiculo.created_at).days if vehiculo.created_at else 0

    is_stale = dias_en_estado >= _STALE_DAYS and estado != EstadoOperativo.CERRADO

    # ── Última venta ───────────────────────────────────────────────────────────
    last_sale = (
        LineaRepuesto.objects.filter(
            origen_repuesto=ORIGEN_DESARME,
            pieza_desarme__vehiculo_desarme=vehiculo,
        )
        .order_by("-id")
        .values_list("documento__fecha_emision", flat=True)
        .first()
    )
    dias_sin_venta: int | None = None
    if last_sale:
        dias_sin_venta = (now.date() - last_sale).days if last_sale else None

    # ── Días en patio ──────────────────────────────────────────────────────────
    if vehiculo.fecha_ingreso_desarme:
        dias_en_patio = (now.date() - vehiculo.fecha_ingreso_desarme).days
    else:
        dias_en_patio = dias_en_estado

    # ── Sección: header ────────────────────────────────────────────────────────
    header = {
        "nombre": f"{vehiculo.anio or ''} {vehiculo.get_marca_display()} {vehiculo.get_modelo_display()}".strip(),
        "estado": estado,
        "estado_label": _STATE_LABEL.get(estado, estado),
        "estado_tone": _STATE_TONE.get(estado, "slate"),
        "dias_en_estado": dias_en_estado,
        "es_cerrado": estado == EstadoOperativo.CERRADO,
    }

    # ── Sección: progress ──────────────────────────────────────────────────────
    progress_pct = _PROGRESS_BY_STATE.get(estado, 10)
    progress_steps = [
        {"key": EstadoOperativo.INGRESADO,        "label": "Ingresado",        "done": progress_pct >= 10},
        {"key": EstadoOperativo.EN_REVISION,       "label": "En revisión",      "done": progress_pct >= 30},
        {"key": EstadoOperativo.EN_PROCESAMIENTO,  "label": "En proceso",       "done": progress_pct >= 60},
        {"key": EstadoOperativo.EN_CIERRE,         "label": "En cierre",        "done": progress_pct >= 85},
        {"key": EstadoOperativo.CERRADO,           "label": "Cerrado",          "done": progress_pct >= 100},
    ]
    progress = {
        "pct": progress_pct,
        "steps": progress_steps,
        "current_state": estado,
    }

    # ── Sección: next_action ───────────────────────────────────────────────────
    next_action = _compute_next_action(
        estado=estado,
        vehiculo=vehiculo,
        disponibles=disponibles,
        sin_precio=sin_precio,
        sin_publicar=sin_publicar,
        publicadas=publicadas,
        sug_pendientes=sug_pendientes,
        sug_total=sug_total,
        is_stale=is_stale,
        dias_en_estado=dias_en_estado,
        dias_sin_venta=dias_sin_venta,
        total_piezas=total_piezas,
        vendidas_count=vendidas_count,
        pct_recuperado=pct_recuperado,
        costo_total=costo_total,
        total_recaudado=total_recaudado,
        request=request,
    )

    # ── Sección: KPIs adaptativos ──────────────────────────────────────────────
    kpis = _compute_kpis(
        estado=estado,
        vehiculo=vehiculo,
        piezas=piezas,
        disponibles=disponibles,
        publicadas=publicadas,
        sin_precio=sin_precio,
        vendidas_count=vendidas_count,
        sug_pendientes=sug_pendientes,
        sug_confirmadas=sug_confirmadas,
        sug_descartadas=sug_descartadas,
        costo_compra=costo_compra,
        costo_total=costo_total,
        total_recaudado=total_recaudado,
        pct_recuperado=pct_recuperado,
        dias_en_patio=dias_en_patio,
    )

    # ── Sección: parts_summary ─────────────────────────────────────────────────
    parts_summary = {
        "total": total_piezas,
        "disponibles": len(disponibles),
        "publicadas": len(publicadas),
        "sin_publicar": len(sin_publicar),
        "sin_precio": len(sin_precio),
        "vendidas": vendidas_count,
        "danadas": danadas_count,
        "faltantes": faltantes_count,
        "valor_potencial": valor_potencial,
    }

    # ── Sección: alerts ────────────────────────────────────────────────────────
    alerts = _compute_alerts(
        estado=estado,
        sin_precio=sin_precio,
        is_stale=is_stale,
        dias_en_estado=dias_en_estado,
        dias_sin_venta=dias_sin_venta,
        publicadas=publicadas,
        sug_total=sug_total,
        total_piezas=total_piezas,
        request=request,
        vehiculo=vehiculo,
    )

    # ── Sección: quick_actions ─────────────────────────────────────────────────
    quick_actions = _compute_quick_actions(
        estado=estado,
        vehiculo=vehiculo,
        sin_publicar=sin_publicar,
        sin_precio=sin_precio,
        request=request,
    )

    # ── Sección: activity (timeline) ──────────────────────────────────────────
    activity = _compute_activity(empresa=empresa, vehiculo=vehiculo)

    # ── Sección: data_quality ──────────────────────────────────────────────────
    data_quality = _compute_data_quality(vehiculo=vehiculo, piezas=piezas)

    return {
        "header": header,
        "progress": progress,
        "next_action": next_action,
        "kpis": kpis,
        "parts_summary": parts_summary,
        "alerts": alerts,
        "quick_actions": quick_actions,
        "activity": activity,
        "data_quality": data_quality,
    }


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _compute_next_action(
    *,
    estado,
    vehiculo,
    disponibles,
    sin_precio,
    sin_publicar,
    publicadas,
    sug_pendientes,
    sug_total,
    is_stale,
    dias_en_estado,
    dias_sin_venta,
    total_piezas,
    vendidas_count,
    pct_recuperado,
    costo_total,
    total_recaudado,
    request,
) -> dict:
    pk = vehiculo.pk

    if estado == EstadoOperativo.CERRADO:
        return {
            "key": "VEHICULO_CERRADO",
            "priority": 100,
            "tone": "emerald",
            "title": "Vehículo cerrado",
            "description": f"Recuperaste el {pct_recuperado:.0f}% de la inversión.",
            "button_label": None,
            "url": None,
        }

    # Priority 10 — Integridad: piezas publicadas sin precio
    piezas_pub_sin_precio = [p for p in publicadas if not p["precio_venta_sugerido"] or p["precio_venta_sugerido"] == Decimal("0")]
    if piezas_pub_sin_precio:
        return {
            "key": "PIEZAS_PUBLICADAS_SIN_PRECIO",
            "priority": 10,
            "tone": "red",
            "title": f"{len(piezas_pub_sin_precio)} pieza{'s' if len(piezas_pub_sin_precio)>1 else ''} publicada{'s' if len(piezas_pub_sin_precio)>1 else ''} sin precio",
            "description": "No puede aparecer en el kiosko con precio en cero. Asigna precio antes de publicar.",
            "button_label": "Ver piezas",
            "url": _build_url(request, f"piezas/?vehiculo={pk}"),
        }

    # Priority 20 — Bloqueado/estancado
    if is_stale:
        return {
            "key": "VEHICULO_ESTANCADO",
            "priority": 20,
            "tone": "amber",
            "title": f"Lleva {dias_en_estado} días en «{_STATE_LABEL.get(estado, estado)}»",
            "description": "Revisá si hay piezas bloqueadas o si el vehículo puede avanzar de etapa.",
            "button_label": "Ver piezas" if estado != EstadoOperativo.INGRESADO else "Iniciar revisión",
            "url": (
                _build_url(request, f"piezas/?vehiculo={pk}")
                if estado != EstadoOperativo.INGRESADO
                else _build_url(request, f"vehiculos/{pk}/revisar/")
            ),
        }

    # Priority 30 — INGRESADO con revisión sin iniciar
    if estado == EstadoOperativo.INGRESADO:
        if sug_total == 0:
            return {
                "key": "REVISION_NO_INICIADA",
                "priority": 30,
                "tone": "cyan",
                "title": "Todavía no se revisó el vehículo",
                "description": "El primer paso es revisar qué piezas se pueden recuperar.",
                "button_label": "Iniciar revisión",
                "url": _build_url(request, f"vehiculos/{pk}/revisar/"),
            }
        return {
            "key": "REVISION_EN_CURSO",
            "priority": 30,
            "tone": "cyan",
            "title": "Revisión en curso",
            "description": f"Completá la revisión para avanzar al procesamiento.",
            "button_label": "Continuar revisión",
            "url": _build_url(request, f"vehiculos/{pk}/revisar/"),
        }

    # Priority 35 — EN_REVISION con sugerencias pendientes
    if estado == EstadoOperativo.EN_REVISION and sug_pendientes > 0:
        return {
            "key": "SUGERENCIAS_PENDIENTES",
            "priority": 35,
            "tone": "amber",
            "title": f"{sug_pendientes} pieza{'s' if sug_pendientes>1 else ''} pendiente{'s' if sug_pendientes>1 else ''} de confirmar",
            "description": "Confirmá o descartá cada pieza para avanzar al procesamiento.",
            "button_label": "Continuar revisión",
            "url": _build_url(request, f"vehiculos/{pk}/revisar/"),
        }

    # Priority 50 — Disponibles sin publicar
    if sin_publicar:
        return {
            "key": "PIEZAS_SIN_PUBLICAR",
            "priority": 50,
            "tone": "cyan",
            "title": f"{len(sin_publicar)} pieza{'s' if len(sin_publicar)>1 else ''} lista{'s' if len(sin_publicar)>1 else ''} para publicar",
            "description": "Las piezas están en stock pero no visibles en el kiosko todavía.",
            "button_label": "Ver piezas",
            "url": _build_url(request, f"piezas/?vehiculo={pk}"),
        }

    # Priority 55 — Disponibles sin precio
    if sin_precio and not sin_publicar:
        return {
            "key": "PIEZAS_SIN_PRECIO",
            "priority": 55,
            "tone": "amber",
            "title": f"{len(sin_precio)} pieza{'s' if len(sin_precio)>1 else ''} sin precio asignado",
            "description": "Sin precio no se puede publicar ni cotizar.",
            "button_label": "Ver piezas",
            "url": _build_url(request, f"piezas/?vehiculo={pk}"),
        }

    # Priority 60 — Publicadas sin movimiento
    if publicadas and dias_sin_venta is not None and dias_sin_venta >= _NO_SALES_WARNING_DAYS:
        return {
            "key": "SIN_VENTAS_RECIENTES",
            "priority": 60,
            "tone": "amber",
            "title": f"Sin ventas hace {dias_sin_venta} días",
            "description": "Considerá revisar los precios o aumentar la visibilidad.",
            "button_label": "Ver piezas",
            "url": _build_url(request, f"piezas/?vehiculo={pk}"),
        }
    if publicadas and dias_sin_venta is None:
        return {
            "key": "PUBLICADO_SIN_VENTAS",
            "priority": 62,
            "tone": "amber",
            "title": "Piezas publicadas pero sin ventas registradas",
            "description": "Verificá que los precios y fotos estén completos.",
            "button_label": "Ver piezas",
            "url": _build_url(request, f"piezas/?vehiculo={pk}"),
        }

    # Priority 70 — Todo vendido, listo para cierre
    if total_piezas > 0 and len(disponibles) == 0 and vendidas_count > 0:
        return {
            "key": "LISTO_PARA_CIERRE",
            "priority": 70,
            "tone": "emerald",
            "title": "Todas las piezas vendidas",
            "description": "El vehículo puede cerrarse. Revisá chatarra y costos adicionales.",
            "button_label": "Ver vehículo",
            "url": _build_url(request, f"vehiculos/{pk}/"),
        }

    # Priority 80 — Todo en orden
    if publicadas:
        return {
            "key": "TODO_PUBLICADO",
            "priority": 80,
            "tone": "emerald",
            "title": "Piezas publicadas y activas",
            "description": f"Recuperaste el {pct_recuperado:.0f}% de la inversión. Seguí así.",
            "button_label": None,
            "url": None,
        }

    return {
        "key": "SIN_TAREAS",
        "priority": 80,
        "tone": "slate",
        "title": "Sin tareas pendientes",
        "description": "El vehículo está al día.",
        "button_label": None,
        "url": None,
    }


def _compute_kpis(
    *,
    estado,
    vehiculo,
    piezas,
    disponibles,
    publicadas,
    sin_precio,
    vendidas_count,
    sug_pendientes,
    sug_confirmadas,
    sug_descartadas,
    costo_compra,
    costo_total,
    total_recaudado,
    pct_recuperado,
    dias_en_patio,
) -> list[dict]:
    if estado == EstadoOperativo.INGRESADO:
        return [
            {
                "label": "Costo de compra",
                "value": costo_compra,
                "type": "money",
                "tone": "slate",
            },
            {
                "label": "Días en patio",
                "value": dias_en_patio,
                "type": "number",
                "tone": "slate" if dias_en_patio < _STALE_DAYS else "amber",
            },
            {
                "label": "Piezas registradas",
                "value": len(piezas),
                "type": "number",
                "tone": "slate",
            },
        ]

    if estado == EstadoOperativo.EN_REVISION:
        return [
            {
                "label": "Pendientes de revisar",
                "value": sug_pendientes,
                "type": "number",
                "tone": "amber" if sug_pendientes > 0 else "emerald",
            },
            {
                "label": "Confirmadas",
                "value": sug_confirmadas,
                "type": "number",
                "tone": "emerald",
            },
            {
                "label": "Descartadas",
                "value": sug_descartadas,
                "type": "number",
                "tone": "slate",
            },
        ]

    if estado == EstadoOperativo.EN_PROCESAMIENTO:
        return [
            {
                "label": "En stock",
                "value": len(disponibles),
                "type": "number",
                "tone": "cyan",
            },
            {
                "label": "Publicadas en kiosko",
                "value": len(publicadas),
                "type": "number",
                "tone": "emerald" if publicadas else "amber",
            },
            {
                "label": "Sin precio",
                "value": len(sin_precio),
                "type": "number",
                "tone": "red" if sin_precio else "emerald",
            },
            {
                "label": "Vendidas",
                "value": vendidas_count,
                "type": "number",
                "tone": "blue",
            },
        ]

    # EN_CIERRE, CERRADO
    ganancia = total_recaudado - costo_total
    return [
        {
            "label": "Recaudado",
            "value": total_recaudado,
            "type": "money",
            "tone": "blue",
        },
        {
            "label": "Costo total",
            "value": costo_total,
            "type": "money",
            "tone": "slate",
        },
        {
            "label": "Ganancia neta",
            "value": ganancia,
            "type": "money",
            "tone": "emerald" if ganancia >= 0 else "red",
        },
        {
            "label": "% recuperado",
            "value": f"{pct_recuperado:.0f}%",
            "type": "text",
            "tone": "emerald" if pct_recuperado >= 100 else ("amber" if pct_recuperado >= 50 else "red"),
        },
    ]


def _compute_alerts(
    *,
    estado,
    sin_precio,
    is_stale,
    dias_en_estado,
    dias_sin_venta,
    publicadas,
    sug_total,
    total_piezas,
    request,
    vehiculo,
) -> list[dict]:
    alerts = []
    pk = vehiculo.pk

    # Piezas sin precio (no publicadas)
    sin_precio_no_pub = [p for p in sin_precio if not p["publicada"]]
    if sin_precio_no_pub and estado not in (EstadoOperativo.INGRESADO, EstadoOperativo.EN_REVISION):
        alerts.append({
            "key": "SIN_PRECIO",
            "tone": "amber",
            "text": f"{len(sin_precio_no_pub)} pieza{'s' if len(sin_precio_no_pub)>1 else ''} sin precio — no se pueden publicar.",
            "url": _build_url(request, f"piezas/?vehiculo={pk}"),
            "url_label": "Ver piezas",
        })

    # Publicadas sin movimiento
    if publicadas and dias_sin_venta is not None and dias_sin_venta >= _NO_SALES_WARNING_DAYS:
        alerts.append({
            "key": "SIN_VENTAS",
            "tone": "amber",
            "text": f"Sin ventas hace {dias_sin_venta} días. Revisá precios.",
            "url": _build_url(request, f"piezas/?vehiculo={pk}"),
            "url_label": "Ver piezas",
        })

    # Revisión nunca iniciada (INGRESADO sin sugerencias)
    if estado == EstadoOperativo.INGRESADO and sug_total == 0 and total_piezas == 0:
        alerts.append({
            "key": "SIN_REVISION",
            "tone": "cyan",
            "text": "La revisión del vehículo no ha comenzado.",
            "url": _build_url(request, f"vehiculos/{pk}/revisar/"),
            "url_label": "Iniciar revisión",
        })

    return alerts


def _compute_quick_actions(
    *,
    estado,
    vehiculo,
    sin_publicar,
    sin_precio,
    request,
) -> list[dict]:
    pk = vehiculo.pk
    actions = []

    if estado == EstadoOperativo.INGRESADO:
        actions.append({
            "key": "INICIAR_REVISION",
            "label": "Iniciar revisión",
            "url": _build_url(request, f"vehiculos/{pk}/revisar/"),
            "tone": "cyan",
        })

    if estado == EstadoOperativo.EN_REVISION:
        actions.append({
            "key": "CONTINUAR_REVISION",
            "label": "Continuar revisión",
            "url": _build_url(request, f"vehiculos/{pk}/revisar/"),
            "tone": "cyan",
        })

    if estado in (EstadoOperativo.EN_PROCESAMIENTO, EstadoOperativo.EN_CIERRE):
        actions.append({
            "key": "VER_PIEZAS",
            "label": "Ver piezas",
            "url": _build_url(request, f"piezas/?vehiculo={pk}"),
            "tone": "cyan",
        })

    if estado == EstadoOperativo.CERRADO:
        actions.append({
            "key": "VER_HISTORIAL",
            "label": "Ver historial",
            "url": _build_url(request, f"vehiculos/{pk}/"),
            "tone": "slate",
        })

    return actions


def _compute_activity(*, empresa, vehiculo) -> list[dict]:
    """Returns the last 20 operational events for the timeline."""
    events = (
        VehiculoDesarmeEvent.objects.filter(
            empresa=empresa,
            vehiculo=vehiculo,
        )
        .order_by("-occurred_at")[:20]
    )

    result = []
    for ev in events:
        is_migration = ev.tipo == TipoEventoDesarme.MIGRACION_ESTADO_INICIAL
        label = _event_label(ev.tipo, ev.metadata)
        result.append({
            "tipo": ev.tipo,
            "label": label,
            "occurred_at": ev.occurred_at,
            "is_migration": is_migration,
            "meta": ev.metadata,
            "created_by": ev.created_by_id,
        })
    return result


def _event_label(tipo: str, meta: dict) -> str:
    if tipo == TipoEventoDesarme.ESTADO_OPERATIVO_CAMBIADO:
        desde = _STATE_LABEL.get(meta.get("from", ""), meta.get("from", ""))
        hasta = _STATE_LABEL.get(meta.get("to", ""), meta.get("to", ""))
        return f"Estado: {desde} → {hasta}"
    if tipo == TipoEventoDesarme.MIGRACION_ESTADO_INICIAL:
        estado_inf = meta.get("estado_operativo", "")
        label = _STATE_LABEL.get(estado_inf, estado_inf)
        return f"Historial operativo iniciado con estado «{label}»"

    labels = {
        TipoEventoDesarme.VEHICULO_CREADO:       "Vehículo creado",
        TipoEventoDesarme.REVISION_INICIADA:     "Revisión iniciada",
        TipoEventoDesarme.REVISION_FINALIZADA:   "Revisión finalizada",
        TipoEventoDesarme.PIEZA_CONFIRMADA:      "Pieza confirmada",
        TipoEventoDesarme.PIEZA_DESCARTADA:      "Pieza descartada",
        TipoEventoDesarme.PIEZA_DESMONTADA:      "Pieza desmontada",
        TipoEventoDesarme.PIEZA_ALMACENADA:      "Pieza almacenada",
        TipoEventoDesarme.PIEZA_PUBLICADA:       "Pieza publicada",
        TipoEventoDesarme.PIEZA_DESPUBLICADA:    "Pieza despublicada",
        TipoEventoDesarme.PIEZA_RESERVADA:       "Pieza reservada",
        TipoEventoDesarme.PIEZA_VENDIDA:         "Pieza vendida",
        TipoEventoDesarme.VENTA_ANULADA:         "Venta anulada",
        TipoEventoDesarme.COSTO_REGISTRADO:      "Costo registrado",
        TipoEventoDesarme.CIERRE_INICIADO:       "Cierre iniciado",
        TipoEventoDesarme.VEHICULO_CERRADO:      "Vehículo cerrado",
    }
    return labels.get(tipo, tipo)


def _compute_data_quality(*, vehiculo, piezas) -> list[dict]:
    """Returns a list of missing data issues (informational, no actions)."""
    issues = []
    if not vehiculo.precio_compra:
        issues.append({"key": "SIN_COSTO_COMPRA", "text": "Sin costo de compra registrado."})
    if not vehiculo.fecha_ingreso_desarme:
        issues.append({"key": "SIN_FECHA_INGRESO", "text": "Sin fecha de ingreso registrada."})
    if not vehiculo.vendedor_desarme_id:
        issues.append({"key": "SIN_PROVEEDOR", "text": "Sin proveedor registrado."})
    return issues
