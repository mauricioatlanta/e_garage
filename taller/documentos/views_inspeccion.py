"""
Vistas para Inspección de Ingreso de Vehículos.
Flujo: OT → detalle → "Registrar Inspección" → form → detalle inspección.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from taller.models.documento import Documento
from taller.models.inspeccion_ingreso import (
    DanoInspeccion,
    EvidenciaInspeccion,
    InspeccionIngreso,
    NIVEL_COMBUSTIBLE,
    ZONAS_VEHICULO,
    TIPOS_DANO,
    ESTADO_INSPECCION,
)


@login_required
def crear_inspeccion_ingreso(request, documento_id):
    empresa = request.user.empresa
    documento = get_object_or_404(Documento, pk=documento_id, empresa=empresa)

    # Si ya existe, redirigir al detalle
    if hasattr(documento, "inspeccion_ingreso"):
        return redirect("documentos:ver_inspeccion_ingreso", pk=documento.inspeccion_ingreso.pk)

    if request.method == "POST":
        inspeccion = InspeccionIngreso(
            empresa=empresa,
            documento=documento,
            vehiculo=documento.vehiculo,
            realizada_por=request.user,
        )
        inspeccion.kilometraje_ingreso = request.POST.get("kilometraje_ingreso") or None
        inspeccion.nivel_combustible = request.POST.get("nivel_combustible", "medio")
        inspeccion.observaciones_generales = request.POST.get("observaciones_generales", "")
        inspeccion.firma_cliente = bool(request.POST.get("firma_cliente"))
        inspeccion.estado_inspeccion = "completada" if inspeccion.firma_cliente else "pendiente"
        inspeccion.save()

        # Daños (puede haber varios: zona_0, tipo_dano_0, descripcion_0, ...)
        i = 0
        while f"zona_{i}" in request.POST:
            zona = request.POST.get(f"zona_{i}", "").strip()
            tipo = request.POST.get(f"tipo_dano_{i}", "").strip()
            desc = request.POST.get(f"descripcion_{i}", "").strip()
            if zona and tipo:
                DanoInspeccion.objects.create(
                    inspeccion=inspeccion, zona=zona, tipo_dano=tipo, descripcion=desc
                )
            i += 1

        # Fotos (hasta 10 por inspección)
        for archivo in request.FILES.getlist("fotos"):
            ext = archivo.name.rsplit(".", 1)[-1].lower()
            tipo = "VIDEO" if ext in ("mp4", "mov", "avi", "webm") else "FOTO"
            desc = request.POST.get(f"desc_foto_{EvidenciaInspeccion.objects.filter(inspeccion=inspeccion).count()}", "")
            EvidenciaInspeccion.objects.create(
                inspeccion=inspeccion,
                tipo=tipo,
                archivo=archivo,
                descripcion=desc,
            )

        messages.success(request, "Inspección de ingreso registrada.")
        return redirect("documentos:ver_inspeccion_ingreso", pk=inspeccion.pk)

    ctx = {
        "documento": documento,
        "nivel_combustible_choices": NIVEL_COMBUSTIBLE,
        "zonas_choices": ZONAS_VEHICULO,
        "tipos_dano_choices": TIPOS_DANO,
    }
    return render(request, "taller/documentos/inspeccion_ingreso_form.html", ctx)


@login_required
def ver_inspeccion_ingreso(request, pk):
    empresa = request.user.empresa
    inspeccion = get_object_or_404(InspeccionIngreso, pk=pk, empresa=empresa)
    ctx = {
        "inspeccion": inspeccion,
        "danos": inspeccion.danos.all(),
        "evidencias": inspeccion.evidencias.all(),
    }
    return render(request, "taller/documentos/inspeccion_ingreso_detalle.html", ctx)


@login_required
@require_POST
def marcar_firmada(request, pk):
    empresa = request.user.empresa
    inspeccion = get_object_or_404(InspeccionIngreso, pk=pk, empresa=empresa)
    inspeccion.firma_cliente = True
    inspeccion.estado_inspeccion = "firmada"
    inspeccion.save(update_fields=["firma_cliente", "estado_inspeccion"])
    messages.success(request, "Inspección marcada como firmada por el cliente.")
    return redirect("documentos:ver_inspeccion_ingreso", pk=inspeccion.pk)
