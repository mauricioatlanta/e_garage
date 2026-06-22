"""
Señales para manejo de inventario (stock) en documentos

Detecta cambios de estado del documento y actualiza stock automáticamente:
- BORRADOR → EMITIDO: Descontar stock
- EMITIDO → ANULADO: Reponer stock
- ANULADO → EMITIDO: Descontar stock nuevamente
- Ediciones: Ajustar diferencia

Importante: Estas señales solo procesan cambios de estado.
La validación de stock debe hacerse ANTES en la vista.
"""

import logging

from django.db import transaction
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, ORIGEN_DESARME
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


@receiver(post_save, sender=Documento, dispatch_uid="inventory_liberar_reservas_al_cambiar_estado")
def liberar_reservas_al_cambiar_estado(sender, instance, created, **kwargs):
    """
    Libera piezas RESERVADAS cuando el documento ya no está en BORRADOR.

    BORRADOR → EMITIDO: _actualizar_stock_desarme ya marcó VENDIDA las que llegaron a 0.
      Aquí liberamos las que quedaron con cantidad > 0 (ya no están comprometidas).
    BORRADOR → ANULADO: el stock nunca se descontó; liberamos sin tocar cantidades.
    """
    if created:
        return
    estado_anterior = getattr(instance, "_estado_anterior_inventario", None)
    if estado_anterior != "BORRADOR":
        return
    if instance.estado not in ("EMITIDO", "ANULADO"):
        return
    if instance.tipo in InventoryService.TIPOS_SIN_STOCK:
        return

    lineas_desarme = instance.lineas_repuesto.filter(
        origen_repuesto=ORIGEN_DESARME
    ).values_list("pieza_desarme_id", flat=True)

    for pieza_id in lineas_desarme:
        if pieza_id:
            InventoryService.liberar_pieza_si_libre(pieza_id)
            log.debug(f"[InventorySignal] Pieza {pieza_id} liberada tras {estado_anterior}→{instance.estado}")


@receiver(post_save, sender=LineaRepuesto, dispatch_uid="inventory_reservar_pieza_al_crear_linea")
def reservar_pieza_al_crear_linea(sender, instance, created, **kwargs):
    """
    Al agregar una pieza de desarme a cualquier documento (OT/FAC), la reserva
    inmediatamente para que el kiosko no la muestre como disponible.
    """
    if not created:
        return
    if instance.origen_repuesto != ORIGEN_DESARME or not instance.pieza_desarme_id:
        return
    # Presupuestos no mueven stock
    if Documento.objects.filter(
        pk=instance.documento_id, tipo__in=InventoryService.TIPOS_SIN_STOCK
    ).exists():
        return
    InventoryService.reservar_pieza(instance.pieza_desarme_id)
    log.info(f"[InventorySignal] Pieza {instance.pieza_desarme_id} → RESERVADA (línea {instance.pk} creada en doc {instance.documento_id})")


@receiver(post_delete, sender=LineaRepuesto, dispatch_uid="inventory_liberar_pieza_al_borrar_linea")
def liberar_pieza_al_borrar_linea(sender, instance, **kwargs):
    """
    Al eliminar una línea de desarme, libera la pieza si ningún otro documento
    BORRADOR sigue usándola. Cubre tanto borrado manual como CASCADE desde Documento.
    """
    if instance.origen_repuesto != ORIGEN_DESARME or not instance.pieza_desarme_id:
        return
    InventoryService.liberar_pieza_si_libre(instance.pieza_desarme_id)
    log.debug(f"[InventorySignal] Pieza {instance.pieza_desarme_id} verificada para liberación (línea {instance.pk} eliminada)")
