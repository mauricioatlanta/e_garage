"""
Vistas para manejo de inventario (emisión, anulación, validación de stock)
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from taller.models.documento import Documento
from taller.services.inventory_service import InventoryService


@login_required
@require_POST
def emitir_documento(request, documento_id):
    """
    Emite un documento (cambia estado a EMITIDO) validando stock disponible.

    La señal pre_save se encargará de descontar el stock automáticamente.
    """
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        messages.error(request, "Usuario sin empresa asociada.")
        return redirect("documentos:lista_documentos")

    documento = get_object_or_404(
        Documento.objects.select_related("empresa", "cliente").prefetch_related(
            "lineas_repuesto__repuesto"
        ),
        id=documento_id,
        empresa=empresa,  # 🔒 Multi-tenant
    )

    # Validar que no esté ya emitido
    if documento.estado == "EMITIDO":
        messages.warning(request, f"El documento {documento.numero_documento} ya está emitido.")
        return redirect("documentos:ver_documento", pk=documento.pk)

    # Validar que no esté anulado
    if documento.estado == "ANULADO":
        messages.error(
            request, f"No se puede emitir un documento anulado ({documento.numero_documento})."
        )
        return redirect("documentos:ver_documento", pk=documento.pk)

    # Validar stock disponible ANTES de cambiar estado
    errores = InventoryService.validar_stock_disponible(documento)

    if errores:
        messages.error(request, f"No se puede emitir el documento {documento.numero_documento}:")
        for error in errores:
            messages.error(request, error)
        return redirect("documentos:ver_documento", pk=documento.pk)

    # Si pasa validación, cambiar estado (la señal procesará el stock)
    try:
        with transaction.atomic():
            documento.estado = "EMITIDO"
            documento.save()
            messages.success(
                request,
                f"✅ Documento {documento.numero_documento} emitido exitosamente. "
                "Stock actualizado automáticamente.",
            )
    except Exception as e:
        messages.error(request, f"Error al emitir documento: {str(e)}")

    return redirect("documentos:ver_documento", pk=documento.pk)


@login_required
@require_POST
def anular_documento(request, documento_id):
    """
    Anula un documento (cambia estado a ANULADO) reponiendo stock automáticamente.

    La señal pre_save se encargará de reponer el stock automáticamente.
    """
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        messages.error(request, "Usuario sin empresa asociada.")
        return redirect("documentos:lista_documentos")

    documento = get_object_or_404(
        Documento.objects.select_related("empresa"),
        id=documento_id,
        empresa=empresa,  # 🔒 Multi-tenant
    )

    # Validar que esté emitido
    if documento.estado != "EMITIDO":
        messages.error(
            request,
            f"Solo se pueden anular documentos emitidos. "
            f"Estado actual: {documento.get_estado_display()}",
        )
        return redirect("documentos:ver_documento", pk=documento.pk)

    # Cambiar estado (la señal procesará la reposición de stock)
    try:
        with transaction.atomic():
            documento.estado = "ANULADO"
            documento.save()
            messages.success(
                request,
                f"✅ Documento {documento.numero_documento} anulado. "
                "Stock repuesto automáticamente.",
            )
    except Exception as e:
        messages.error(request, f"Error al anular documento: {str(e)}")

    return redirect("documentos:ver_documento", pk=documento.pk)


@login_required
def validar_stock_documento(request, documento_id):
    """
    Vista para validar stock de un documento (sin emitirlo).
    Útil para mostrar warnings antes de emitir.
    """
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        messages.error(request, "Usuario sin empresa asociada.")
        return redirect("documentos:lista_documentos")

    documento = get_object_or_404(
        Documento.objects.select_related("empresa").prefetch_related("lineas_repuesto__repuesto"),
        id=documento_id,
        empresa=empresa,  # 🔒 Multi-tenant
    )

    errores = InventoryService.validar_stock_disponible(documento)

    if errores:
        messages.warning(
            request, f"⚠️ Problemas de stock en documento {documento.numero_documento}:"
        )
        for error in errores:
            messages.warning(request, error)
    else:
        messages.success(request, f"✅ Stock suficiente para emitir {documento.numero_documento}.")

    return redirect("documentos:ver_documento", pk=documento.pk)
