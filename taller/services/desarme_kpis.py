"""
KPIs y resumen operativo del vehículo de desarme.
Lógica centralizada para dashboard financiero, mapa y reportes.
"""

from decimal import Decimal
from typing import Dict, Any, List

from taller.models import Vehiculo


STATUS_TO_FRONTEND = {
    "disponible": "available",
    "dañado": "damaged",
    "scrap": "scrap",
    "vendido": "sold",
    "reservada": "reserved",
    "": "unreviewed",
    None: "unreviewed",
}
STATUS_TO_BACKEND = {
    "available": "disponible",
    "damaged": "dañado",
    "scrap": "scrap",
    "sold": "vendido",
    "reserved": "reservada",
    "unreviewed": "",
}


def build_vehicle_desarme_kpis(vehiculo: Vehiculo) -> Dict[str, Any]:
    """
    Construye el diccionario completo de KPIs para dashboard financiero.
    Costos, ingresos, resultado, progreso económico. No duplicar en vistas.
    """
    costo_base = vehiculo.costo_total_base
    costos_adicionales = vehiculo.costos_adicionales_total
    costo_total = vehiculo.costo_total_desarme
    ingresos_repuestos = vehiculo.ingresos_repuestos_total
    ingreso_chatarra = vehiculo.ingreso_final_chatarra or Decimal("0")
    ingresos_totales = vehiculo.ingresos_totales
    utilidad = vehiculo.utilidad_total
    pct = float(vehiculo.porcentaje_recuperacion)
    faltante = costo_total - ingresos_totales
    ya_supero = ingresos_totales >= costo_total and costo_total > 0

    return {
        "costo_total_base": str(costo_base),
        "costos_adicionales_total": str(costos_adicionales),
        "costo_total": str(costo_total),
        "ingresos_repuestos": str(ingresos_repuestos),
        "ingreso_final_chatarra": str(ingreso_chatarra),
        "ingresos_totales": str(ingresos_totales),
        "utilidad_total": str(utilidad),
        "porcentaje_recuperacion": round(pct, 1),
        "faltante_recuperar": str(faltante),
        "faltante_por_recuperar": str(max(Decimal("0"), faltante)),
        "ya_supero_costo": ya_supero,
    }


def get_kpis(vehiculo: Vehiculo) -> Dict[str, Any]:
    """Calcula KPIs del vehículo de desarme (compatibilidad mapa/resumen)."""
    k = build_vehicle_desarme_kpis(vehiculo)
    return {
        "costo_total": k["costo_total"],
        "ingresos_repuestos": k["ingresos_repuestos"],
        "ingreso_final_chatarra": k["ingreso_final_chatarra"],
        "ingresos_totales": k["ingresos_totales"],
        "utilidad_total": k["utilidad_total"],
        "porcentaje_recuperacion": k["porcentaje_recuperacion"],
        "faltante_recuperar": k["faltante_recuperar"],
    }


def get_piece_summary(vehiculo: Vehiculo, solo_con_zona: bool = True) -> Dict[str, Any]:
    """Cuenta piezas por estado. Si solo_con_zona=False, cuenta todas las piezas del vehículo."""
    qs = vehiculo.repuestos_desarme
    if solo_con_zona:
        qs = qs.filter(zona_mapa__isnull=False).exclude(zona_mapa="")
    repuestos = list(qs.values("estado_pieza"))
    c = {"disponible": 0, "dañado": 0, "scrap": 0, "vendido": 0, "reservada": 0}
    for r in repuestos:
        e = (r.get("estado_pieza") or "").strip()
        if e in c:
            c[e] += 1
    total = len(repuestos)
    revisadas = sum(c.values())
    pendientes = total - revisadas
    return {
        "total": total,
        "disponible": c["disponible"],
        "damaged": c["dañado"],
        "dañado": c["dañado"],
        "scrap": c["scrap"],
        "vendido": c["vendido"],
        "reservada": c["reservada"],
        "available": c["disponible"],
        "sold": c["vendido"],
        "reserved": c["reservada"],
        "piezas_revisadas": revisadas,
        "pendientes": pendientes,
        "progreso_pct": round(revisadas / total * 100, 1) if total else 0,
    }


def build_vehicle_piece_summary(vehiculo: Vehiculo) -> Dict[str, Any]:
    """Resumen de piezas para dashboard (todas las piezas del vehículo)."""
    return get_piece_summary(vehiculo, solo_con_zona=False)


def build_vehicle_sales_summary(vehiculo: Vehiculo, limit: int = 15) -> List[Dict[str, Any]]:
    """
    Últimas ventas de piezas del vehículo (líneas de documento emitidas).
    Para reportes y dashboard. Cada ítem: documento, fecha, repuesto, cantidad, subtotal.
    """
    from django.db.models import DecimalField, ExpressionWrapper, F, Value
    from django.db.models.functions import Coalesce

    from taller.models import LineaRepuesto

    lineas = (
        LineaRepuesto.objects.filter(
            repuesto__vehiculo_origen=vehiculo,
            documento__estado="EMITIDO",
        )
        .select_related("documento", "repuesto")
        .order_by("-documento__fecha_emision", "-id")[:limit]
    )
    result = []
    for lin in lineas:
        subtotal = (lin.cantidad or 0) * (lin.precio_unitario or 0)
        if getattr(lin, "descuento", None):
            subtotal *= 1 - (float(lin.descuento or 0) / 100)
        result.append(
            {
                "documento_id": lin.documento_id,
                "documento_tipo": getattr(lin.documento, "tipo", ""),
                "fecha": lin.documento.fecha_emision if lin.documento else None,
                "repuesto_nombre": lin.nombre or (lin.repuesto.nombre if lin.repuesto else ""),
                "cantidad": int(lin.cantidad or 0),
                "precio_unitario": str(lin.precio_unitario or "0"),
                "subtotal": str(round(subtotal, 2)),
            }
        )
    return result
