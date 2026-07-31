"""
Vistas para manejo de inventario (emisión, anulación, validación de stock)
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from taller.models.documento import Documento
from taller.models.lineas_documento import ORIGEN_DESARME, ORIGEN_STOCK_BODEGA
from taller.models.pieza_desarme import ESTADO_DISPONIBLE, PiezaDesarme
from taller.models.repuesto import Repuesto
from taller.services.inventory_service import InventoryService


@login_required
@require_POST
def emitir_documento(request, documento_id):
    """
    Emite un documento (cambia estado a EMITIDO) validando stock disponible.

    Patrón: SELECT FOR UPDATE → validar → save → signal descuenta.
    - DESARME: lock en PiezaDesarme, validación con objetos bloqueados.
    - STOCK_BODEGA: lock en Repuesto antes de validar_stock_disponible(),
      evitando TOCTOU entre emisiones concurrentes del mismo repuesto.
    - EXTERNO: no mueve stock, no requiere lock.
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

    if documento.estado == "EMITIDO":
        messages.warning(request, f"El documento {documento.numero_documento} ya está emitido.")
        return redirect("documentos:ver_documento", pk=documento.pk)

    if documento.estado == "ANULADO":
        messages.error(
            request, f"No se puede emitir un documento anulado ({documento.numero_documento})."
        )
        return redirect("documentos:ver_documento", pk=documento.pk)

    errores_validacion = []
    try:
        with transaction.atomic():
            # ── Piezas de desarme: lock + validación con datos bloqueados ────────
            lineas_desarme = list(
                documento.lineas_repuesto
                .filter(origen_repuesto=ORIGEN_DESARME, pieza_desarme_id__isnull=False)
                .select_related("pieza_desarme")
            )
            if lineas_desarme:
                pieza_ids = [l.pieza_desarme_id for l in lineas_desarme]
                locked = {
                    p.id: p
                    for p in PiezaDesarme.objects.select_for_update().filter(id__in=pieza_ids)
                }
                for linea in lineas_desarme:
                    pieza = locked[linea.pieza_desarme_id]
                    if pieza.estado_pieza != ESTADO_DISPONIBLE:
                        errores_validacion.append(
                            f"❌ Pieza '{pieza.nombre}' no está disponible "
                            f"(estado: {pieza.get_estado_pieza_display()})."
                        )
                    elif pieza.cantidad < linea.cantidad:
                        errores_validacion.append(
                            f"❌ Stock insuficiente en '{pieza.nombre}'. "
                            f"Requerido: {linea.cantidad}, Disponible: {pieza.cantidad}"
                        )

            # ── Repuestos de bodega: lock + validación ────────────────────────────
            # SELECT FOR UPDATE antes de leer cantidad_stock previene que dos
            # emisiones concurrentes validen contra el mismo saldo y descuenten doble.
            repuesto_ids_bodega = list(
                documento.lineas_repuesto.filter(
                    origen_repuesto=ORIGEN_STOCK_BODEGA, repuesto_id__isnull=False
                ).values_list("repuesto_id", flat=True)
            )
            if repuesto_ids_bodega:
                list(
                    Repuesto.objects.select_for_update().filter(
                        id__in=repuesto_ids_bodega, empresa=empresa
                    )
                )
            if not errores_validacion:
                errores_validacion = InventoryService.validar_stock_disponible(documento)

            if errores_validacion:
                raise ValueError("stock_insuficiente")

            documento.estado = "EMITIDO"
            documento.save()  # → pre_save signal → procesar_movimiento_stock("descontar")
    except ValueError:
        messages.error(request, f"No se puede emitir el documento {documento.numero_documento}:")
        for error in errores_validacion:
            messages.error(request, error)
    except Exception as e:
        messages.error(request, f"Error al emitir documento: {str(e)}")
    else:
        messages.success(
            request,
            f"✅ Documento {documento.numero_documento} emitido exitosamente. "
            "Stock actualizado automáticamente.",
        )

    return redirect("documentos:ver_documento", pk=documento.pk)


@login_required
@require_POST
def anular_documento(request, documento_id):
    """
    Anula un documento (cambia estado a ANULADO) reponiendo stock automáticamente.

    La señal pre_save repone la cantidad en PiezaDesarme y revierte VENDIDA → DISPONIBLE
    si la pieza vuelve a tener stock. También repone STOCK_BODEGA.

    # TODO: cuando exista DatosDTE, condicionar esta reversión al estado del DTE
    # (no revertir automáticamente si ya se emitió un documento fiscal real)
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

    if documento.estado != "EMITIDO":
        messages.error(
            request,
            f"Solo se pueden anular documentos emitidos. "
            f"Estado actual: {documento.get_estado_display()}",
        )
        return redirect("documentos:ver_documento", pk=documento.pk)

    try:
        with transaction.atomic():
            documento.estado = "ANULADO"
            documento.save()  # → pre_save signal → procesar_movimiento_stock("reponer")
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
