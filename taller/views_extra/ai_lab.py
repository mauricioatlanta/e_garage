"""
AI Lab dashboard: placeholders con datos reales (sin LLM externo).
Módulos: predicción de carga semanal, sugerencias de ventas, historial inteligente.
"""

import logging
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils import timezone

from taller.auth.country_login_required import country_login_required
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio

logger = logging.getLogger(__name__)


@country_login_required
def ai_lab_dashboard(request):
    """
    AI Lab: 3 módulos con datos históricos (predicción, sugerencias, historial).
    Sin LLM externo; todo calculado con datos internos.
    """
    try:
        empresa = request.user.empresa
    except Exception:
        if "/cl/" in request.path:
            return redirect("chile:configuracion")
        if "/us/" in request.path:
            return redirect("usa:configuracion")
        return redirect("configuracion")

    hoy = timezone.localdate()
    hace_8_semanas = hoy - timedelta(weeks=8)
    hace_30_dias = hoy - timedelta(days=30)
    inicio_mes = hoy.replace(day=1)

    # --- 1) Predicción de carga semanal (últimas 8 semanas, promedio por día) ---
    docs_por_semana = []
    for i in range(8):
        inicio_sem = hace_8_semanas + timedelta(weeks=i)
        fin_sem = inicio_sem + timedelta(days=7)
        cnt = Documento.objects.filter(
            empresa=empresa,
            fecha_emision__gte=inicio_sem,
            fecha_emision__lt=fin_sem,
        ).count()
        docs_por_semana.append({"semana": i + 1, "total": cnt, "promedio_dia": round(cnt / 7, 1)})

    promedio_general = sum(s["total"] for s in docs_por_semana) / (8 * 7) if docs_por_semana else 0
    prediccion_carga = {
        "semanas": docs_por_semana,
        "promedio_documentos_por_dia": round(promedio_general, 1),
        "mensaje": f"Basado en las últimas 8 semanas: ~{round(promedio_general, 1)} documentos/día.",
    }

    # --- 2) Sugerencias de ventas: top servicios/repuestos último mes + "ofrecer X" ---
    top_servicios = (
        LineaServicio.objects.filter(
            documento__empresa=empresa,
            documento__fecha_emision__gte=inicio_mes,
            documento__tipo="FAC",
        )
        .values("nombre")
        .annotate(cantidad=Count("id"))
        .order_by("-cantidad")[:5]
    )
    top_repuestos = (
        LineaRepuesto.objects.filter(
            documento__empresa=empresa,
            documento__fecha_emision__gte=inicio_mes,
            documento__tipo="FAC",
        )
        .values("nombre")
        .annotate(cantidad=Count("id"))
        .order_by("-cantidad")[:5]
    )

    sugerencias = []
    for s in list(top_servicios)[:3]:
        nombre = (s.get("nombre") or "Servicio")[:40]
        cantidad = s.get("cantidad") or 0
        sugerencias.append(
            {
                "tipo": "servicio",
                "nombre": nombre,
                "cantidad": cantidad,
                "accion": f"Ofrecer: {nombre}",
            }
        )
    for r in list(top_repuestos)[:2]:
        nombre = (r.get("nombre") or "Repuesto")[:40]
        cantidad = r.get("cantidad") or 0
        sugerencias.append(
            {
                "tipo": "repuesto",
                "nombre": nombre,
                "cantidad": cantidad,
                "accion": f"Ofrecer: {nombre}",
            }
        )

    sugerencias_ventas = {
        "items": sugerencias[:5],
        "mensaje": "Top servicios y repuestos del mes para potenciar ventas.",
    }

    # --- 3) Historial inteligente: últimos 5 documentos + patrones (cliente recurrente, vehículo repetido) ---
    ultimos_5 = (
        Documento.objects.filter(empresa=empresa)
        .select_related("cliente", "vehiculo")
        .order_by("-fecha_emision", "-id")[:5]
    )

    cliente_ids = [d.cliente_id for d in ultimos_5 if d.cliente_id]
    vehiculo_ids = [d.vehiculo_id for d in ultimos_5 if d.vehiculo_id and d.vehiculo_id]

    # Patrones: clientes con más de 1 doc en los últimos 5
    conteo_cliente = defaultdict(int)
    for d in ultimos_5:
        if d.cliente_id:
            conteo_cliente[d.cliente_id] += 1
    recurrentes = [cid for cid, n in conteo_cliente.items() if n > 1]

    conteo_vehiculo = defaultdict(int)
    for d in ultimos_5:
        if d.vehiculo_id:
            conteo_vehiculo[d.vehiculo_id] += 1
    vehiculos_repetidos = [vid for vid, n in conteo_vehiculo.items() if n > 1]

    historial_inteligente = {
        "ultimos_documentos": list(ultimos_5),
        "patron_clientes_recurrentes": len(recurrentes) > 0,
        "patron_vehiculos_repetidos": len(vehiculos_repetidos) > 0,
        "mensaje": "Últimos documentos y patrones detectados (cliente recurrente, mismo vehículo).",
    }

    from django.urls import reverse

    back_url = reverse("chile:dashboard")
    context = {
        "empresa": empresa,
        "prediccion_carga": prediccion_carga,
        "sugerencias_ventas": sugerencias_ventas,
        "historial_inteligente": historial_inteligente,
        "moneda": getattr(empresa, "simbolo_moneda", "$"),
        "back_url": back_url,
    }

    return TemplateResponse(
        request,
        "taller/common/ai_lab/ai_lab_home.html",
        context,
    )
