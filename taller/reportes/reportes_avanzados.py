"""
📊 REPORTES AVANZADOS CON SERVICIOS SUBCONTRATADOS
================================================

Reportes visuales para análisis de rentabilidad y servicios externos
"""

from collections import defaultdict
from datetime import date, timedelta

from django.db import models
from django.db.models import (Avg, Count, ExpressionWrapper, F, FloatField,
                              Max, Min, Q, Sum)
from django.shortcuts import render

from taller.models.clientes import Cliente
from taller.models.lineas_documento import (LineaOtroServicio, LineaRepuesto,
                                            LineaServicio)
from taller.models.vehiculos import Vehiculo


def reportes_rentabilidad(request):
    """
    🎯 Reporte de rentabilidad por tipo de servicio
    """
    # Servicios internos - rentabilidad (usamos LineaServicio)
    servicios_internos = (
        LineaServicio.objects.filter(documento__tipo="FAC")
        .values("servicio")
        .annotate(
            cantidad=Count("id"),
            ingresos_totales=Sum("precio_unitario"),
            precio_promedio=Avg("precio_unitario"),
        )
        .order_by("-ingresos_totales")[:15]
    )

    # Servicios subcontratados - análisis de rentabilidad (LineaOtroServicio)
    servicios_externos = (
        LineaOtroServicio.objects.filter(documento__tipo="FAC")
        .values("nombre_servicio", "empresa_externa")
        .annotate(
            cantidad=Count("id"),
            ingresos_totales=Sum("precio_cliente"),
            costos_totales=Sum("costo_interno"),
            ganancia_total=Sum(F("precio_cliente") - F("costo_interno")),
            precio_promedio=Avg("precio_cliente"),
        )
        .order_by("-ganancia_total")[:15]
    )

    # Comparativa rentabilidad: interno vs externo
    total_interno = (
        LineaServicio.objects.filter(documento__tipo="FAC").aggregate(
            total=Sum("precio_unitario")
        )["total"]
        or 0
    )

    total_externo_ingresos = (
        LineaOtroServicio.objects.filter(documento__tipo="FAC").aggregate(
            total=Sum("precio_cliente")
        )["total"]
        or 0
    )

    total_externo_costos = (
        LineaOtroServicio.objects.filter(documento__tipo="FAC").aggregate(
            total=Sum("costo_interno")
        )["total"]
        or 0
    )

    ganancia_externa = total_externo_ingresos - total_externo_costos

    # Top proveedores externos por volumen
    top_proveedores = (
        LineaOtroServicio.objects.filter(documento__tipo="FAC")
        .values("empresa_externa")
        .annotate(
            cantidad_servicios=Count("id"),
            volumen_total=Sum("precio_cliente"),
            costo_total=Sum("costo_interno"),
            ganancia_total=Sum(F("precio_cliente") - F("costo_interno")),
        )
        .order_by("-volumen_total")[:10]
    )

    # Servicios más rentables (margen %)
    servicios_alto_margen = []
    for servicio in LineaOtroServicio.objects.filter(documento__tipo="FAC"):
        precio_cliente = getattr(servicio, "precio_cliente", None)
        costo_interno = getattr(servicio, "costo_interno", None)
        if not precio_cliente:
            continue
        margen = ((precio_cliente - (costo_interno or 0)) / precio_cliente) * 100
        servicios_alto_margen.append(
            {
                "nombre": getattr(servicio, "nombre_servicio", "N/A"),
                "proveedor": getattr(servicio, "empresa_externa", "N/A"),
                "margen": round(margen, 2),
                "ganancia": (precio_cliente - (costo_interno or 0)),
                "precio_cliente": precio_cliente,
                "costo_interno": costo_interno,
            }
        )

    servicios_alto_margen = sorted(
        servicios_alto_margen, key=lambda x: x["margen"], reverse=True
    )[:10]

    context = {
        "servicios_internos": servicios_internos,
        "servicios_externos": servicios_externos,
        "total_interno": total_interno,
        "total_externo_ingresos": total_externo_ingresos,
        "total_externo_costos": total_externo_costos,
        "ganancia_externa": ganancia_externa,
        "top_proveedores": top_proveedores,
        "servicios_alto_margen": servicios_alto_margen,
    }

    return render(request, "taller/reportes/rentabilidad.html", context)


def reporte_comparativo_precios(request):
    """
    💰 Comparativa precio cliente vs. costo proveedor
    """
    # Análisis detallado por servicio
    analisis_servicios = []

    servicios_unicos = (
        LineaOtroServicio.objects.filter(documento__tipo="FAC")
        .values("nombre_servicio")
        .distinct()
    )

    for servicio in servicios_unicos:
        nombre = servicio["nombre_servicio"]
        registros = LineaOtroServicio.objects.filter(nombre_servicio=nombre)

        stats = registros.aggregate(
            cantidad=Count("id"),
            precio_promedio=Avg("precio_cliente"),
            costo_promedio=Avg("costo_interno"),
            precio_max=Max("precio_cliente"),
            precio_min=Min("precio_cliente"),
            costo_max=Max("costo_interno"),
            costo_min=Min("costo_interno"),
            ganancia_total=Sum(F("precio_cliente") - F("costo_interno")),
        )

        if stats["precio_promedio"] and stats["costo_promedio"]:
            margen_promedio = (
                (stats["precio_promedio"] - stats["costo_promedio"])
                / stats["precio_promedio"]
            ) * 100

            analisis_servicios.append(
                {
                    "nombre": nombre,
                    "cantidad": stats["cantidad"],
                    "precio_promedio": round(stats["precio_promedio"], 2),
                    "costo_promedio": round(stats["costo_promedio"], 2),
                    "margen_promedio": round(margen_promedio, 2),
                    "ganancia_total": stats["ganancia_total"],
                    "precio_rango": f"${stats['precio_min']:,} - ${stats['precio_max']:,}",
                    "costo_rango": f"${stats['costo_min']:,} - ${stats['costo_max']:,}",
                }
            )

    analisis_servicios = sorted(
        analisis_servicios, key=lambda x: x["ganancia_total"], reverse=True
    )

    # Alertas de márgenes bajos
    margenes_bajos = [s for s in analisis_servicios if s["margen_promedio"] < 20]

    # Evolución mensual de márgenes
    hoy = date.today()
    hace_6_meses = hoy - timedelta(days=180)

    evolucion_mensual = (
        LineaOtroServicio.objects.filter(
            documento__tipo="FAC", documento__fecha_emision__gte=hace_6_meses
        )
        .annotate(
            mes=F("documento__fecha_emision__year") * 100
            + F("documento__fecha_emision__month")
        )
        .values("mes")
        .annotate(
            ingresos=Sum("precio_cliente"),
            costos=Sum("costo_interno"),
        )
        .order_by("mes")
    )

    context = {
        "analisis_servicios": analisis_servicios,
        "margenes_bajos": margenes_bajos,
        "evolucion_mensual": list(evolucion_mensual),
    }

    return render(request, "taller/reportes/comparativo_precios.html", context)


def reporte_servicios_subcontratados(request):
    """
    🔧 Servicios subcontratados más frecuentes
    """
    # Servicios más frecuentes
    servicios_frecuentes = (
        LineaOtroServicio.objects.values("nombre_servicio")
        .annotate(
            frecuencia=Count("id"),
            volumen_total=Sum("precio_cliente"),
            ganancia_total=Sum(F("precio_cliente") - F("costo_interno")),
        )
        .order_by("-frecuencia")[:15]
    )

    proveedores_frecuentes = (
        LineaOtroServicio.objects.values("empresa_externa")
        .annotate(
            servicios_realizados=Count("id"),
            tipos_servicios=Count("nombre_servicio", distinct=True),
            volumen_total=Sum("precio_cliente"),
            ganancia_generada=Sum(F("precio_cliente") - F("costo_interno")),
        )
        .order_by("-servicios_realizados")[:10]
    )
    # Análisis temporal - últimos 6 meses
    hoy = date.today()
    hace_6_meses = hoy - timedelta(days=180)

    tendencia_mensual = defaultdict(lambda: {"cantidad": 0, "volumen": 0})

    servicios_periodo = LineaOtroServicio.objects.filter(
        documento__fecha_emision__gte=hace_6_meses
    )

    for servicio in servicios_periodo:
        mes_key = (
            servicio.documento.fecha_emision.strftime("%Y-%m")
            if servicio.documento.fecha_emision
            else "Sin fecha"
        )
        tendencia_mensual[mes_key]["cantidad"] += 1
        tendencia_mensual[mes_key]["volumen"] += servicio.precio_cliente

    # Preparar datos para gráficos
    meses = sorted(tendencia_mensual.keys())
    cantidades = [tendencia_mensual[mes]["cantidad"] for mes in meses]
    volumenes = [tendencia_mensual[mes]["volumen"] for mes in meses]

    # Distribución por tipo de vehículo
    vehiculos_servicios = (
        LineaOtroServicio.objects.filter(documento__vehiculo__isnull=False)
        .values(
            "documento__vehiculo__marca__nombre", "documento__vehiculo__modelo__nombre"
        )
        .annotate(cantidad=Count("id"))
        .order_by("-cantidad")[:10]
    )

    # Clientes que más usan servicios externos
    clientes_externos = (
        LineaOtroServicio.objects.values(
            "documento__cliente__id",
            "documento__cliente__nombre",
            "documento__cliente__apellido",
        )
        .annotate(servicios_externos=Count("id"), gasto_total=Sum("precio_cliente"))
        .order_by("-gasto_total")[:10]
    )

    for cliente in clientes_externos:
        nombre = cliente.get("documento__cliente__nombre") or ""
        apellido = cliente.get("documento__cliente__apellido") or ""
        cliente["nombre_completo"] = f"{nombre} {apellido}".strip()

    context = {
        "servicios_frecuentes": servicios_frecuentes,
        "proveedores_frecuentes": proveedores_frecuentes,
        "tendencia_meses": meses,
        "tendencia_cantidades": cantidades,
        "tendencia_volumenes": volumenes,
        "vehiculos_servicios": vehiculos_servicios,
        "clientes_externos": clientes_externos,
    }

    return render(request, "taller/reportes/servicios_subcontratados.html", context)


def dashboard_rentabilidad(request):
    """
    📈 Dashboard general de rentabilidad
    """
    # KPIs principales
    total_facturado = (
        LineaServicio.objects.filter(documento__tipo="FAC").aggregate(
            total=Sum("precio_unitario")
        )["total"]
        or 0
    ) + (
        LineaOtroServicio.objects.filter(documento__tipo="FAC").aggregate(
            total=Sum("precio_cliente")
        )["total"]
        or 0
    )

    costos_externos = (
        LineaOtroServicio.objects.filter(documento__tipo="FAC").aggregate(
            total=Sum("costo_interno")
        )["total"]
        or 0
    )

    ganancia_neta = total_facturado - costos_externos

    # Distribución de ingresos
    ingresos_internos = (
        LineaServicio.objects.filter(documento__tipo="FAC").aggregate(
            total=Sum("precio_unitario")
        )["total"]
        or 0
    )
    ingresos_externos = (
        LineaOtroServicio.objects.filter(documento__tipo="FAC").aggregate(
            total=Sum("precio_cliente")
        )["total"]
        or 0
    )

    # Mejores y peores márgenes por proveedor
    proveedor_margenes = (
        LineaOtroServicio.objects.filter(documento__tipo="FAC")
        .values("empresa_externa")
        .annotate(
            margen_promedio=Avg(
                ExpressionWrapper(
                    (F("precio_cliente") - F("costo_interno"))
                    * 100.0
                    / F("precio_cliente"),
                    output_field=FloatField(),
                )
            )
        )
    )

    mejor_proveedor = (
        proveedor_margenes.order_by("-margen_promedio").first()
        if proveedor_margenes
        else None
    )
    peor_proveedor = (
        proveedor_margenes.order_by("margen_promedio").first()
        if proveedor_margenes
        else None
    )

    margen_general = (ganancia_neta * 100.0 / total_facturado) if total_facturado else 0

    context = {
        "total_facturado": total_facturado,
        "costos_externos": costos_externos,
        "ganancia_neta": ganancia_neta,
        "margen_general": round(margen_general, 2),
        "ingresos_internos": ingresos_internos,
        "ingresos_externos": ingresos_externos,
        "mejor_proveedor": mejor_proveedor,
        "peor_proveedor": peor_proveedor,
    }

    return render(request, "taller/reportes/dashboard_rentabilidad.html", context)
