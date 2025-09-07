"""
Vistas para el módulo de inteligencia de negocio
"""

import json
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, F, Q, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from taller.auth.decorators import login_required_default
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto as RepuestoDocumento
from taller.models.lineas_documento import LineaServicio as LineaServicio
from taller.models.repuesto import Repuesto
from taller.models.tecnico import Tecnico


@login_required_default
def dashboard_business_intelligence(request):
    """Dashboard principal de inteligencia de negocio"""
    try:
        # Obtener empresa directamente del usuario
        empresa = request.user.empresa

        if not empresa:
            return render(
                request,
                "error.html",
                {
                    "error": "Tu usuario no tiene una empresa asociada. Por favor, contacta al administrador."
                },
            )

    except AttributeError:
        return render(
            request,
            "error.html",
            {
                "error": "No tienes una empresa configurada. Por favor, contacta al administrador para configurar tu acceso."
            },
        )

    # Obtener fechas para filtros
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)  # Último mes por defecto

    # Obtener parámetros de filtro
    if request.GET.get("fecha_inicio"):
        fecha_inicio = datetime.strptime(
            request.GET.get("fecha_inicio"), "%Y-%m-%d"
        ).date()
    if request.GET.get("fecha_fin"):
        fecha_fin = datetime.strptime(request.GET.get("fecha_fin"), "%Y-%m-%d").date()

    # Datos para el dashboard
    context = {
        "empresa": empresa,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "servicios_ranking": get_servicios_ranking(empresa, fecha_inicio, fecha_fin),
        "repuestos_utilidad": get_repuestos_utilidad(empresa, fecha_inicio, fecha_fin),
        "tecnicos_stats": get_tecnicos_stats(empresa, fecha_inicio, fecha_fin),
        "resumen_general": get_resumen_general(empresa, fecha_inicio, fecha_fin),
    }

    return render(request, "business_intelligence/dashboard.html", context)


def get_servicios_ranking(empresa, fecha_inicio, fecha_fin):
    """Obtiene el ranking de servicios más vendidos"""
    servicios = (
        LineaServicio.objects.filter(
            documento__empresa=empresa,
            documento__fecha_emision__range=[fecha_inicio, fecha_fin],
        )
        .values("nombre")
        .annotate(
            cantidad_vendida=Count("id"),
            ingresos_totales=Sum(F("precio_unitario") * F("cantidad")),
            precio_promedio=Avg(F("precio_unitario")),
        )
        .order_by("-cantidad_vendida")[:10]
    )

    return list(servicios)


def get_repuestos_utilidad(empresa, fecha_inicio, fecha_fin):
    """Calcula la utilidad neta por repuesto"""
    repuestos_vendidos = (
        RepuestoDocumento.objects.filter(
            documento__empresa=empresa,
            documento__fecha_emision__range=[fecha_inicio, fecha_fin],
            repuesto__isnull=False,
        )
        .select_related("repuesto")
        .values(
            "repuesto__nombre",
            "repuesto__part_number",
            "repuesto__precio_venta",
            "repuesto__precio_compra",
        )
        .annotate(
            cantidad_vendida=Sum("cantidad"),
            ingresos_totales=Sum(F("cantidad") * F("precio_unitario")),
        )
    )

    utilidades = []
    for repuesto in repuestos_vendidos:
        precio_venta = repuesto["repuesto__precio_venta"]
        precio_compra = repuesto["repuesto__precio_compra"]
        cantidad = repuesto["cantidad_vendida"]
        ingresos = repuesto["ingresos_totales"]

        costo_total = precio_compra * cantidad
        utilidad_bruta = ingresos - costo_total
        margen_utilidad = (utilidad_bruta / ingresos * 100) if ingresos > 0 else 0

        utilidades.append(
            {
                "nombre": repuesto["repuesto__nombre"],
                "part_number": repuesto["repuesto__part_number"],
                "cantidad_vendida": cantidad,
                "ingresos_totales": ingresos,
                "costo_total": costo_total,
                "utilidad_bruta": utilidad_bruta,
                "margen_utilidad": round(margen_utilidad, 2),
                "precio_venta": precio_venta,
                "precio_compra": precio_compra,
            }
        )

    return sorted(utilidades, key=lambda x: x["utilidad_bruta"], reverse=True)[:10]


def get_tecnicos_stats(empresa, fecha_inicio, fecha_fin):
    """Obtiene estadísticas por técnico"""
    try:
        tecnicos = Tecnico.objects.filter(empresa=empresa, activo=True)
        stats = []

        for tecnico in tecnicos:
            # Intentar usar tecnico_responsable, pero manejar el error si la columna no existe
            try:
                documentos = Documento.objects.filter(
                    empresa=empresa,
                    tecnico_responsable=tecnico,
                    fecha_emision__range=[fecha_inicio, fecha_fin],
                )
                total_documentos = documentos.count()
            except Exception as e:
                # Si la columna tecnico_responsable no existe, usar todos los documentos
                # (esto es temporal hasta que se ejecuten las migraciones)
                print(f"Warning: Campo tecnico_responsable no disponible: {e}")
                documentos = Documento.objects.filter(
                    empresa=empresa, fecha_emision__range=[fecha_inicio, fecha_fin]
                )
                total_documentos = documentos.count() // max(
                    tecnicos.count(), 1
                )  # Distribuir equitativamente

            # Calcular totales

            # Agregar repuestos vendidos de forma separada
            repuestos_queryset = RepuestoDocumento.objects.filter(
                documento__in=documentos
            )
            total_repuestos_cantidad = sum(r.cantidad for r in repuestos_queryset)
            total_repuestos_valor = sum(
                r.cantidad * getattr(r, "precio_unitario", getattr(r, "precio", 0))
                for r in repuestos_queryset
            )

            # Agregar servicios realizados
            try:
                servicios_stats = LineaServicio.objects.filter(
                    documento__in=documentos
                ).aggregate(
                    cantidad=Count("id"),
                    valor=Sum(F("precio_unitario") * F("cantidad")),
                )
            except Exception as e:
                print(f"Error calculando servicios_stats: {e}")
                servicios_stats = {"cantidad": 0, "valor": 0}

            ingresos_totales = total_repuestos_valor + (servicios_stats["valor"] or 0)

            stats.append(
                {
                    "tecnico": tecnico,
                    "total_documentos": total_documentos,
                    "repuestos_vendidos": total_repuestos_cantidad,
                    "servicios_realizados": servicios_stats["cantidad"] or 0,
                    "ingresos_totales": ingresos_totales,
                    "promedio_por_documento": (
                        round(ingresos_totales / total_documentos, 2)
                        if total_documentos > 0
                        else 0
                    ),
                }
            )

        return sorted(stats, key=lambda x: x["ingresos_totales"], reverse=True)
    except Exception as e:
        print(f"Error en get_tecnicos_stats: {e}")
        return []


def get_resumen_general(empresa, fecha_inicio, fecha_fin):
    """Obtiene un resumen general del período"""
    documentos = Documento.objects.filter(
        empresa=empresa, fecha_emision__range=[fecha_inicio, fecha_fin]
    )

    total_repuestos = RepuestoDocumento.objects.filter(
        documento__in=documentos
    ).aggregate(
        total_cantidad=Sum("cantidad"), valor=Sum(F("cantidad") * F("precio_unitario"))
    )

    total_servicios = LineaServicio.objects.filter(documento__in=documentos).aggregate(
        total_servicios=Count("id"), valor=Sum(F("precio_unitario") * F("cantidad"))
    )

    return {
        "total_documentos": documentos.count(),
        "total_repuestos_vendidos": total_repuestos["total_cantidad"] or 0,
        "valor_repuestos": total_repuestos["valor"] or 0,
        "total_servicios_realizados": total_servicios["total_servicios"] or 0,
        "valor_servicios": total_servicios["valor"] or 0,
        "ingresos_totales": (total_repuestos["valor"] or 0)
        + (total_servicios["valor"] or 0),
        "promedio_diario": round(
            ((total_repuestos["valor"] or 0) + (total_servicios["valor"] or 0))
            / max((fecha_fin - fecha_inicio).days, 1),
            2,
        ),
    }


@login_required
def api_servicios_ranking(request):
    """API para obtener ranking de servicios en formato JSON"""
    try:
        empresa = request.user.empresa

        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - timedelta(days=30)

        if request.GET.get("fecha_inicio"):
            fecha_inicio = datetime.strptime(
                request.GET.get("fecha_inicio"), "%Y-%m-%d"
            ).date()
        if request.GET.get("fecha_fin"):
            fecha_fin = datetime.strptime(
                request.GET.get("fecha_fin"), "%Y-%m-%d"
            ).date()

        datos = get_servicios_ranking(empresa, fecha_inicio, fecha_fin)
        return JsonResponse({"success": True, "data": datos})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
def api_repuestos_utilidad(request):
    """API para obtener utilidades de repuestos en formato JSON"""
    try:
        empresa = request.user.empresa

        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - timedelta(days=30)

        if request.GET.get("fecha_inicio"):
            fecha_inicio = datetime.strptime(
                request.GET.get("fecha_inicio"), "%Y-%m-%d"
            ).date()
        if request.GET.get("fecha_fin"):
            fecha_fin = datetime.strptime(
                request.GET.get("fecha_fin"), "%Y-%m-%d"
            ).date()

        datos = get_repuestos_utilidad(empresa, fecha_inicio, fecha_fin)
        return JsonResponse({"success": True, "data": datos})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
def api_tecnicos_stats(request):
    """API para obtener estadísticas de técnicos en formato JSON"""
    try:
        empresa = request.user.empresa

        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - timedelta(days=30)

        if request.GET.get("fecha_inicio"):
            fecha_inicio = datetime.strptime(
                request.GET.get("fecha_inicio"), "%Y-%m-%d"
            ).date()
        if request.GET.get("fecha_fin"):
            fecha_fin = datetime.strptime(
                request.GET.get("fecha_fin"), "%Y-%m-%d"
            ).date()

        datos = get_tecnicos_stats(empresa, fecha_inicio, fecha_fin)

        # Convertir objetos a diccionarios para JSON
        datos_json = []
        for stat in datos:
            datos_json.append(
                {
                    "tecnico_nombre": stat["tecnico"].nombre,
                    "total_documentos": stat["total_documentos"],
                    "repuestos_vendidos": stat["repuestos_vendidos"],
                    "servicios_realizados": stat["servicios_realizados"],
                    "ingresos_totales": stat["ingresos_totales"],
                    "promedio_por_documento": stat["promedio_por_documento"],
                }
            )

        return JsonResponse({"success": True, "data": datos_json})

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
