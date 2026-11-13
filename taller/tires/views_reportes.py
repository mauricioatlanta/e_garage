from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from taller.services.empresa_service import get_empresa_safe
from .reports import (
    reporte_compra_venta,
    reporte_venta_por_medida,
    reporte_proveedores_por_medida,
    reporte_mecanicos_vulcanizacion,
)

@login_required
def reportes_vulcanizacion(request):
    empresa = get_empresa_safe(request)
    tab = request.GET.get("tab", "compra-venta")
    medida_filtro = (request.GET.get("medida") or "").strip()
    proveedor_filtro = (request.GET.get("proveedor") or "").strip()

    compra_venta = reporte_compra_venta(empresa)
    por_medida = reporte_venta_por_medida(empresa)
    proveedores = reporte_proveedores_por_medida(empresa)
    mecanicos = reporte_mecanicos_vulcanizacion(empresa)

    if medida_filtro:
        proveedores = [p for p in proveedores if medida_filtro.lower() in p["medida"].lower()]
        por_medida = [m for m in por_medida if medida_filtro.lower() in m["medida"].lower()]
    if proveedor_filtro:
        proveedores = [p for p in proveedores if proveedor_filtro.lower() in (p["proveedor"] or "").lower()]

    # Proveedores únicos para el filtro
    proveedores_unicos = sorted(set(p["proveedor"] for p in reporte_proveedores_por_medida(empresa)))
    medidas_unicas = sorted(set(m["medida"] for m in reporte_venta_por_medida(empresa)))

    return render(request, "taller/tires/reportes_vulcanizacion.html", {
        "empresa": empresa,
        "tab": tab,
        "compra_venta": compra_venta,
        "por_medida": por_medida,
        "proveedores": proveedores,
        "mecanicos": mecanicos,
        "proveedores_unicos": proveedores_unicos,
        "medidas_unicas": medidas_unicas,
        "medida_filtro": medida_filtro,
        "proveedor_filtro": proveedor_filtro,
    })
