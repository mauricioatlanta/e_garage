"""
Señales para manejo de inventario (stock) en documentos

Detecta cambios de estado del documento y actualiza stock automáticamente:
- BORRADOR → EMITIDO: Descontar stock
- EMITIDO → ANULADO: Reponer stock
- ANULADO → EMITIDO: Descontar stock nuevamente
- Ediciones: Ajustar diferencia

Los borradores NO reservan stock. Las piezas de desarme permanecen DISPONIBLE
mientras el documento es borrador; solo cambian a VENDIDA al emitir.
La validación de stock debe hacerse en la vista, con select_for_update(), justo
antes de cambiar el estado a EMITIDO.
"""

import logging

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from taller.models.documento import Documento
from taller.services.inventory_service import InventoryService

log = logging.getLogger(__name__)


@receiver(pre_save, sender=Documento, dispatch_uid="inventory_control_state_change")
def controlar_stock_al_cambiar_estado(sender, instance, **kwargs):
    """
    Controla movimientos de stock cuando cambia el estado del documento.

    Casos manejados:
    1. BORRADOR → EMITIDO: Descontar stock
    2. EMITIDO → ANULADO: Reponer stock
    3. ANULADO → EMITIDO: Descontar stock nuevamente

    Importante: Esto solo procesa el cambio. La validación debe hacerse antes.
    """
    # Si es creación nueva, no hay estado anterior que comparar
    if getattr(instance, "_skip_inventory_signal", False):
        return

    if not instance.pk:
        return

    try:
        documento_anterior = (
            Documento.objects.select_related("empresa")
            .prefetch_related("lineas_repuesto__repuesto")
            .get(pk=instance.pk)
        )
    except Documento.DoesNotExist:
        log.warning(f"[InventorySignal] No se encontró documento anterior con pk={instance.pk}")
        return

    estado_anterior = documento_anterior.estado
    estado_nuevo = instance.estado
    tipo_documento = instance.tipo

    # Propagar estado_anterior al post_save para que las señales de reserva lo lean
    instance._estado_anterior_inventario = estado_anterior

    # Si el estado no cambió, no hacer nada
    if estado_anterior == estado_nuevo:
        return

    # Presupuestos nunca mueven stock (regla de negocio)
    if tipo_documento == "PRES":
        log.debug(
            f"[InventorySignal] Documento {instance.numero} es tipo {tipo_documento}, no mueve stock"
        )
        return

    log.info(
        f"[InventorySignal] 📦 Cambio de estado en Doc {instance.numero}: "
        f"{estado_anterior} → {estado_nuevo} (Tipo: {tipo_documento})"
    )

    # Caso 1: De BORRADOR a EMITIDO → Descontar Stock
    if estado_anterior == "BORRADOR" and estado_nuevo == "EMITIDO":
        log.info(f"[InventorySignal] Emitiendo documento {instance.numero}, descontando stock...")
        # ⚠️ NOTA: La validación de stock debe hacerse ANTES en la vista
        # Aquí solo procesamos el movimiento
        resultado = InventoryService.procesar_movimiento_stock(instance, "descontar")
        if resultado.get("procesado"):
            log.info(f"[InventorySignal] ✅ Stock descontado para Doc {instance.numero}")
        else:
            log.warning(
                f"[InventorySignal] ⚠️ No se pudo descontar stock para Doc {instance.numero}: "
                f"{resultado.get('razon', 'Desconocido')}"
            )

    # Caso 2: De EMITIDO a ANULADO → Reponer Stock
    elif estado_anterior == "EMITIDO" and estado_nuevo == "ANULADO":
        log.info(f"[InventorySignal] Anulando documento {instance.numero}, reponiendo stock...")
        resultado = InventoryService.procesar_movimiento_stock(documento_anterior, "reponer")
        if resultado.get("procesado"):
            log.info(f"[InventorySignal] ✅ Stock repuesto para Doc {instance.numero}")
        else:
            log.warning(
                f"[InventorySignal] ⚠️ No se pudo reponer stock para Doc {instance.numero}: "
                f"{resultado.get('razon', 'Desconocido')}"
            )

    # Caso 3: De ANULADO a EMITIDO (reactivación) → Descontar Stock nuevamente
    elif estado_anterior == "ANULADO" and estado_nuevo == "EMITIDO":
        log.info(f"[InventorySignal] Reactivando documento {instance.numero}, descontando stock...")
        # ⚠️ Validar stock disponible antes de reactivar
        errores = InventoryService.validar_stock_disponible(instance)
        if errores:
            log.error(
                f"[InventorySignal] ❌ No se puede reactivar Doc {instance.numero}: "
                f"Stock insuficiente - {', '.join(errores)}"
            )
            # ⚠️ En una señal es difícil prevenir el guardado, idealmente esto se valida en la vista
            # Pero podemos registrar el error para debugging
        else:
            resultado = InventoryService.procesar_movimiento_stock(instance, "descontar")
            if resultado.get("procesado"):
                log.info(
                    f"[InventorySignal] ✅ Stock descontado al reactivar Doc {instance.numero}"
                )

    # Caso 4: Edición de documento emitido (mismo estado, pero cambió contenido)
    elif estado_anterior == "EMITIDO" and estado_nuevo == "EMITIDO":
        # Verificar si realmente hubo cambios en las líneas
        # Si cambió cantidad o se agregaron/eliminaron líneas, ajustar stock
        log.info(
            f"[InventorySignal] Editando documento emitido {instance.numero}, ajustando stock..."
        )
        try:
            InventoryService.procesar_edicion(documento_anterior, instance)
            log.info(f"[InventorySignal] ✅ Stock ajustado para Doc {instance.numero}")
        except Exception as e:
            log.error(
                f"[InventorySignal] ❌ Error ajustando stock para Doc {instance.numero}: {e}",
                exc_info=True,
            )


@receiver(post_save, sender=Documento, dispatch_uid="inventory_log_state_change")
def registrar_cambio_estado(sender, instance, created, **kwargs):
    """
    Registra cambios de estado en el log para auditoría.
    """
    if created:
        log.info(
            f"[InventorySignal] 📄 Nuevo documento creado: {instance.numero} (Estado: {instance.estado}, Tipo: {instance.tipo})"
        )
    # Los cambios de estado ya se registran en pre_save


