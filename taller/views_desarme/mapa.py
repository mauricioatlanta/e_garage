"""
Mapa interactivo de vehículo para desarme.
Vista principal y endpoints AJAX.
"""

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from taller.models import Vehiculo
from taller.services.desarme_kpis import get_kpis, get_piece_summary, STATUS_TO_FRONTEND
from taller.services.desarme_piece_service import (
    get_piece_by_zone,
    create_or_update_piece,
    _piece_to_frontend,
)
from taller.utils.empresa import get_or_create_empresa


VIEWS_AVAILABLE = ["frontal", "lateral_izq"]
ZONES_BY_VIEW = {
    "frontal": [
        "hood",
        "front_left_headlight",
        "front_right_headlight",
        "grille",
        "front_bumper",
        "front_left_fog",
        "front_right_fog",
    ],
    "lateral_izq": [
        "hood",
        "left_mirror",
        "left_front_door",
        "left_rear_door",
        "left_front_fender",
        "left_rear_fender",
        "left_front_window",
        "left_rear_window",
        "left_front_wheel",
        "left_rear_wheel",
        "trunk",
        "front_bumper",
        "rear_bumper",
        "left_headlight",
        "left_taillight",
    ],
}
VIEW_ALIAS = {
    "left": "lateral_izq",
    "front": "frontal",
    "frontal": "frontal",
    "lateral_izq": "lateral_izq",
}


def _get_vehiculo_desarme(request, pk):
    """Obtiene vehículo de desarme validando tenant y tipo_uso."""
    empresa = get_or_create_empresa(request)
    return get_object_or_404(
        Vehiculo,
        pk=pk,
        empresa=empresa,
        tipo_uso="desarme",
    )


def _build_pieces_by_zone(vehiculo):
    """
    Construye pieces_by_zone en formato frontend.
    Clave: zone (o zone|view si hay colisiones).
    """
    repuestos = vehiculo.repuestos_desarme.filter(zona_mapa__isnull=False).exclude(zona_mapa="")

    pieces_by_zone = {}
    for p in repuestos:
        zona = (p.zona_mapa or "").strip()
        vista = (p.vista_mapa or "").strip()
        key = zona
        pieces_by_zone[key] = {
            "id": p.id,
            "piece_name": p.nombre,
            "status": STATUS_TO_FRONTEND.get((p.estado_pieza or "").strip(), "unreviewed"),
            "price": str(p.precio_venta or "0"),
            "stock": p.cantidad_stock or 1,
            "note": (getattr(p, "observaciones", None) or "")[:500],
            "zone": zona,
            "view": vista,
        }
    return pieces_by_zone


@login_required
def demo_mapa_desarme(request):
    """Demo frontend del mapa (solo visual, datos mock)."""
    return render(request, "taller/desarme/demo_mapa.html")


@login_required
def vehiculo_mapa_desarme(request, pk):
    """
    Vista principal del mapa interactivo.
    GET /desarme/vehiculos/<pk>/mapa/
    """
    vehiculo = _get_vehiculo_desarme(request, pk)
    can_edit = (vehiculo.estado_desarme or "") != "cerrado"

    pieces_by_zone = _build_pieces_by_zone(vehiculo)
    kpis = get_kpis(vehiculo)
    summary = get_piece_summary(vehiculo)

    api_pieza_url = request.build_absolute_uri(
        reverse("taller:desarme:pieza_por_zona", kwargs={"pk": vehiculo.pk})
    )
    resumen_url = request.build_absolute_uri(
        reverse("taller:desarme:resumen_json", kwargs={"pk": vehiculo.pk})
    )

    context = {
        "vehiculo": vehiculo,
        "can_edit": can_edit,
        "views_available": VIEWS_AVAILABLE,
        "zones_by_view": ZONES_BY_VIEW,
        "api_pieza_url": api_pieza_url,
        "resumen_url": resumen_url,
        "pieces_by_zone_json": pieces_by_zone,
        "kpis_json": kpis,
        "piece_summary_json": summary,
        "kpis": kpis,
        "piece_summary": summary,
        "total_piezas": summary.get("total", 0),
        "piezas_revisadas": summary.get("piezas_revisadas", 0),
        "progreso_pct": summary.get("progreso_pct", 0),
    }
    return render(request, "taller/desarme/mapa_piezas.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def pieza_por_zona(request, pk):
    """
    GET ?zone=left_front_door&view=left
    POST JSON: zone, view, piece_name, status, price, stock, note
    """
    vehiculo = _get_vehiculo_desarme(request, pk)

    if request.method == "GET":
        zone = (request.GET.get("zone") or "").strip()
        view = (request.GET.get("view") or "").strip()
        vista = VIEW_ALIAS.get(view, view) or ""
        if not zone:
            return JsonResponse({"ok": False, "error": "zone requerida"}, status=400)

        pieza = get_piece_by_zone(vehiculo, zone, vista)
        if pieza:
            return JsonResponse(
                {
                    "ok": True,
                    "piece": _piece_to_frontend(pieza),
                }
            )
        return JsonResponse(
            {
                "ok": True,
                "piece": None,
                "defaults": {
                    "piece_name": zone.replace("_", " ").title(),
                    "status": "unreviewed",
                    "stock": 1,
                    "zone": zone,
                    "view": vista,
                },
            }
        )

    # POST
    if vehiculo.estado_desarme == "cerrado":
        return JsonResponse(
            {"ok": False, "error": "Vehículo cerrado, no se pueden modificar piezas."}, status=403
        )

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    zone = (data.get("zone") or data.get("zona") or "").strip()
    view = (data.get("view") or data.get("vista") or "").strip()
    vista = VIEW_ALIAS.get(view, view) or ""
    piece_name = (data.get("piece_name") or data.get("nombre") or "").strip()
    status = (data.get("status") or data.get("estado_pieza") or "unreviewed").strip()
    price = data.get("price") or data.get("precio_venta") or "0"
    stock = data.get("stock", 1)
    note = (
        data.get("note") or data.get("observacion_estado") or data.get("observaciones") or ""
    ).strip()[:500]

    if not zone or not piece_name:
        return JsonResponse({"ok": False, "error": "zone y piece_name requeridos"}, status=400)

    try:
        pieza, summary, kpis = create_or_update_piece(
            vehiculo=vehiculo,
            zone=zone,
            view=vista,
            piece_name=piece_name,
            estado_pieza=status,
            precio_venta=str(price),
            stock=stock,
            observacion_estado=note,
        )
        return JsonResponse(
            {
                "ok": True,
                "piece": _piece_to_frontend(pieza),
                "summary": summary,
                "kpis": kpis,
            }
        )
    except ValueError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=403)


@login_required
@require_http_methods(["GET"])
def resumen_json(request, pk):
    """GET /desarme/vehiculos/<pk>/resumen-json/"""
    vehiculo = _get_vehiculo_desarme(request, pk)
    kpis = get_kpis(vehiculo)
    summary = get_piece_summary(vehiculo)
    return JsonResponse(
        {
            "ok": True,
            "kpis": kpis,
            "summary": summary,
        }
    )
