"""
Servicio de gestión de inventario (Inventory Service)

Maneja la lógica de movimientos de stock asegurando integridad.
Reglas:
- Presupuestos (PRES) NUNCA mueven stock
- OT y FAC SÍ mueven stock según origen_repuesto:
  - STOCK_BODEGA: descontar/reponer en Repuesto
  - DESARME: descontar/reponer en PiezaDesarme (al llegar a 0: estado_pieza=VENDIDA, activo=False)
  - EXTERNO: no mover inventario
- Reversión al anular documento.
"""

import logging
from collections import defaultdict
from typing import List, Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from taller.models.documento import Documento
from taller.models.lineas_documento import (
    LineaRepuesto,
    ORIGEN_DESARME,
    ORIGEN_EXTERNO,
    ORIGEN_STOCK_BODEGA,
)
from taller.models.pieza_desarme import (
    PiezaDesarme,
    ESTADO_DISPONIBLE,
    ESTADO_VENDIDA,
)
from taller.models.vehiculo_desarme import VehiculoDesarme
from taller.models.repuesto import Repuesto

log = logging.getLogger(__name__)


class InventoryService:
    """
    Maneja la lógica de movimientos de stock asegurando integridad.

    Reglas por origen_repuesto:
    - STOCK_BODEGA: Repuesto (lógica actual)
    - DESARME: PiezaDesarme
    - EXTERNO: no mover inventario
    """

    TIPOS_SIN_STOCK = ["PRES"]
    TIPOS_CON_STOCK = ["OT", "FAC"]

    @staticmethod
    def snapshot_lineas_repuesto(documento: Documento) -> list[dict]:
        """
        Guarda una fotografia de las lineas que mueven stock antes de que el
        formulario las elimine y recree en una edicion.
        """
        if not documento or not getattr(documento, "pk", None):
            return []

        snapshot = []
        for linea in documento.lineas_repuesto.values(
            "origen_repuesto",
            "repuesto_id",
            "pieza_desarme_id",
            "cantidad",
        ):
            origen = linea.get("origen_repuesto")
            cantidad = int(linea.get("cantidad") or 0)
            if cantidad <= 0:
                continue
            if origen == ORIGEN_STOCK_BODEGA and linea.get("repuesto_id"):
                snapshot.append(
                    {
                        "origen_repuesto": ORIGEN_STOCK_BODEGA,
                        "repuesto_id": int(linea["repuesto_id"]),
                        "pieza_desarme_id": None,
                        "cantidad": cantidad,
                    }
                )
            elif origen == ORIGEN_DESARME and linea.get("pieza_desarme_id"):
                snapshot.append(
                    {
                        "origen_repuesto": ORIGEN_DESARME,
                        "repuesto_id": None,
                        "pieza_desarme_id": int(linea["pieza_desarme_id"]),
                        "cantidad": cantidad,
                    }
                )
        return snapshot

    @staticmethod
    def _build_reserved_stock_map(snapshot_previo: Optional[list[dict]] = None) -> dict:
        reservas = defaultdict(int)
        for item in snapshot_previo or []:
            origen = item.get("origen_repuesto")
            cantidad = int(item.get("cantidad") or 0)
            if cantidad <= 0:
                continue
            if origen == ORIGEN_STOCK_BODEGA and item.get("repuesto_id"):
                reservas[(ORIGEN_STOCK_BODEGA, int(item["repuesto_id"]))] += cantidad
            elif origen == ORIGEN_DESARME and item.get("pieza_desarme_id"):
                reservas[(ORIGEN_DESARME, int(item["pieza_desarme_id"]))] += cantidad
        return reservas

    @staticmethod
    @transaction.atomic
    def procesar_movimiento_stock(
        documento: Documento, accion: str, cantidades_anteriores: Optional[dict] = None
    ):
        """
        Procesa movimiento de stock según la acción solicitada.

        Args:
            documento: Documento a procesar
            accion: 'descontar' | 'reponer' | 'ajustar'
            cantidades_anteriores: Dict {linea_id: cantidad_anterior} para ajustar ediciones

        Returns:
            dict: Resultado del procesamiento con estadísticas

        Flujo para descontar/reponer (EMISION/ANULACION):
          1. Congelar costo_linea (solo descontar) antes del loop para que el
             MovimientoInventario lo capture en costo_unitario.
          2. SELECT FOR UPDATE en Repuesto ordenado por pk → saldo_actual en memoria.
          3. Por cada línea STOCK_BODEGA: F()-update, actualizar mapa, escribir ledger.
          Toda la operación está en el mismo transaction.atomic.
        """
        from taller.models.movimiento_inventario import MovimientoInventario
        from taller.services.inventory_ledger_service import InventoryLedgerService

        if documento.tipo in InventoryService.TIPOS_SIN_STOCK:
            log.debug(
                f"[InventoryService] Documento {documento.numero} es tipo {documento.tipo}, no mueve stock"
            )
            return {"procesado": False, "razon": "Tipo de documento no mueve stock"}

        lineas = documento.lineas_repuesto.select_related("repuesto", "pieza_desarme").all()
        lineas_con_movimiento = [
            ln
            for ln in lineas
            if (ln.origen_repuesto == ORIGEN_STOCK_BODEGA and ln.repuesto_id)
            or (ln.origen_repuesto == ORIGEN_DESARME and ln.pieza_desarme_id)
        ]
        if not lineas_con_movimiento:
            log.debug(
                f"[InventoryService] Documento {documento.numero} no tiene líneas que muevan inventario"
            )
            return {"procesado": False, "razon": "No hay líneas con stock bodega o desarme"}

        multiplier = -1 if accion == "descontar" else 1 if accion == "reponer" else 0
        log.info(
            f"📦 Inventario: Procesando {accion} para Doc {documento.numero} (Tipo: {documento.tipo})"
        )

        # ── 1. Congelar costo_linea ANTES del loop ────────────────────────────
        # Debe preceder a la creación del MovimientoInventario para que
        # costo_unitario reciba el valor congelado en esta transacción.
        # DESARME: ya tiene costo desde pieza.costo_asignado — no se toca.
        # EXTERNO: no llega a lineas_con_movimiento — se omite.
        if accion == "descontar":
            lineas_a_congelar = [
                ln for ln in lineas_con_movimiento
                if ln.origen_repuesto == ORIGEN_STOCK_BODEGA
                and ln.repuesto_id
                and ln.costo_linea is None  # preservar snapshot existente
            ]
            if lineas_a_congelar:
                for ln in lineas_a_congelar:
                    ln.costo_linea = ln.repuesto.precio_compra
                LineaRepuesto.objects.bulk_update(lineas_a_congelar, ["costo_linea"])
                log.info(
                    f"[InventoryService] 💰 costo_linea congelado "
                    f"para {len(lineas_a_congelar)} líneas STOCK_BODEGA "
                    f"en Doc {documento.numero}"
                )

        # ── 2. Bloquear Repuesto en orden pk + mapa de saldo en memoria ───────
        # Solo para descontar/reponer; ajustar opera fuera del ledger.
        # ORDER BY pk previene deadlocks entre transacciones concurrentes.
        saldo_actual: dict = {}
        if accion in ("descontar", "reponer"):
            lineas_bodega = [
                ln for ln in lineas_con_movimiento
                if ln.origen_repuesto == ORIGEN_STOCK_BODEGA and ln.repuesto_id
            ]
            if lineas_bodega:
                rep_ids = sorted({ln.repuesto_id for ln in lineas_bodega})
                saldo_actual = {
                    r.pk: r.cantidad_stock
                    for r in Repuesto.objects.select_for_update()
                    .filter(id__in=rep_ids, empresa=documento.empresa)
                    .order_by("pk")
                }

        # ── 2b. Bloquear PiezaDesarme en orden pk + mapas de estado en memoria ─
        # ORDER BY pk previene deadlocks. Los mapas evitan re-lecturas y permiten
        # encadenar saldo cuando varias líneas referencian la misma pieza.
        saldo_por_pieza: dict = {}
        estado_por_pieza: dict = {}
        activo_por_pieza: dict = {}
        if accion in ("descontar", "reponer"):
            lineas_desarme_list = [
                ln for ln in lineas_con_movimiento
                if ln.origen_repuesto == ORIGEN_DESARME and ln.pieza_desarme_id
            ]
            if lineas_desarme_list:
                pieza_ids = sorted({ln.pieza_desarme_id for ln in lineas_desarme_list})
                locked_piezas = list(
                    PiezaDesarme.objects.select_for_update()
                    .filter(id__in=pieza_ids)
                    .order_by("pk")
                )
                saldo_por_pieza = {p.pk: p.cantidad for p in locked_piezas}
                estado_por_pieza = {p.pk: p.estado_pieza for p in locked_piezas}
                activo_por_pieza = {p.pk: p.activo for p in locked_piezas}

        # ── 3. Loop principal ─────────────────────────────────────────────────
        movimientos = []

        for linea in lineas_con_movimiento:
            if accion == "ajustar" and cantidades_anteriores:
                cantidad_anterior = cantidades_anteriores.get(linea.id, 0)
                diferencia = linea.cantidad - cantidad_anterior
                if diferencia == 0:
                    continue
                cantidad_actualizar = -diferencia
            else:
                cantidad_actualizar = -linea.cantidad if multiplier < 0 else linea.cantidad

            if linea.origen_repuesto == ORIGEN_STOCK_BODEGA and linea.repuesto_id:
                saldo_antes = saldo_actual.get(linea.repuesto_id, linea.repuesto.cantidad_stock)
                saldo_nuevo = saldo_antes + cantidad_actualizar

                filas = Repuesto.objects.filter(
                    id=linea.repuesto_id, empresa=documento.empresa
                ).update(cantidad_stock=F("cantidad_stock") + cantidad_actualizar)
                if filas == 0:
                    log.warning(
                        f"[InventoryService] No se actualizó stock para repuesto {linea.repuesto_id}"
                    )
                    continue

                saldo_actual[linea.repuesto_id] = saldo_nuevo

                movimientos.append(
                    {
                        "origen": ORIGEN_STOCK_BODEGA,
                        "repuesto_id": linea.repuesto_id,
                        "repuesto_nombre": linea.repuesto.nombre,
                        "cantidad": abs(cantidad_actualizar),
                        "accion": "descontado" if cantidad_actualizar < 0 else "repuesto",
                        "stock_anterior": saldo_antes,
                        "stock_actual": saldo_nuevo,
                    }
                )
                log.info(f"  ✅ BODEGA {linea.repuesto.nombre}: {abs(cantidad_actualizar)} u.")

                if accion in ("descontar", "reponer"):
                    tipo_mov = (
                        MovimientoInventario.TipoMovimiento.EMISION
                        if accion == "descontar"
                        else MovimientoInventario.TipoMovimiento.ANULACION
                    )
                    InventoryLedgerService.record_stock_movement(
                        empresa=documento.empresa,
                        tipo=tipo_mov,
                        repuesto=linea.repuesto,
                        documento=documento,
                        linea_repuesto=linea,
                        cantidad_delta=cantidad_actualizar,
                        saldo_resultante=saldo_nuevo,
                        costo_unitario=linea.costo_linea,
                        metadata={
                            "inventory_ledger_version": InventoryLedgerService.HASH_VERSION,
                            "documento_tipo": documento.tipo,
                            "documento_estado": documento.estado,
                            "accion": accion,
                        },
                    )

            elif linea.origen_repuesto == ORIGEN_DESARME and linea.pieza_desarme_id:
                if accion in ("descontar", "reponer"):
                    pieza_id = linea.pieza_desarme_id
                    saldo_antes = saldo_por_pieza.get(pieza_id, linea.pieza_desarme.cantidad)
                    estado_antes = estado_por_pieza.get(pieza_id, linea.pieza_desarme.estado_pieza)
                    activo_antes = activo_por_pieza.get(pieza_id, linea.pieza_desarme.activo)

                    saldo_nuevo = saldo_antes + cantidad_actualizar
                    if saldo_nuevo < 0:
                        raise ValidationError(
                            f"Stock insuficiente para pieza '{linea.pieza_desarme.nombre}'. "
                            f"Saldo: {saldo_antes}, delta: {cantidad_actualizar}."
                        )

                    if saldo_nuevo <= 0:
                        estado_nuevo = ESTADO_VENDIDA
                        activo_nuevo = False
                    elif estado_antes == ESTADO_VENDIDA and saldo_nuevo > 0:
                        estado_nuevo = ESTADO_DISPONIBLE
                        activo_nuevo = True
                    else:
                        estado_nuevo = estado_antes
                        activo_nuevo = activo_antes

                    tipo_mov = (
                        MovimientoInventario.TipoMovimiento.EMISION
                        if accion == "descontar"
                        else MovimientoInventario.TipoMovimiento.ANULACION
                    )
                    idempotency_key = InventoryLedgerService.build_idempotency_key(
                        empresa_id=documento.empresa_id,
                        tipo=tipo_mov,
                        origen_stock=MovimientoInventario.OrigenStock.DESARME,
                        repuesto_id=None,
                        pieza_desarme_id=pieza_id,
                        documento_id=documento.pk,
                        linea_repuesto_id=linea.pk,
                        cantidad_delta=cantidad_actualizar,
                    )
                    existing_mov = MovimientoInventario.objects.filter(
                        idempotency_key=idempotency_key
                    ).first()
                    if existing_mov is not None:
                        # La delta ya fue aplicada en una llamada anterior; el DB
                        # locked refleja ese estado. No tocar mapas ni pieza.
                        movimientos.append({
                            "origen": ORIGEN_DESARME,
                            "pieza_desarme_id": pieza_id,
                            "nombre": linea.pieza_desarme.nombre,
                            "cantidad": abs(cantidad_actualizar),
                            "accion": "descontado" if cantidad_actualizar < 0 else "repuesto",
                        })
                        log.info(f"  ♻️ DESARME {linea.pieza_desarme.nombre}: idempotente.")
                        continue

                    filas = PiezaDesarme.objects.filter(
                        id=pieza_id, empresa=documento.empresa
                    ).update(
                        cantidad=F("cantidad") + cantidad_actualizar,
                        estado_pieza=estado_nuevo,
                        activo=activo_nuevo,
                    )
                    if filas == 0:
                        log.warning(
                            f"[InventoryService] No se actualizó pieza {pieza_id}"
                        )
                        continue

                    saldo_por_pieza[pieza_id] = saldo_nuevo
                    estado_por_pieza[pieza_id] = estado_nuevo
                    activo_por_pieza[pieza_id] = activo_nuevo

                    if saldo_nuevo <= 0:
                        try:
                            veh_id = linea.pieza_desarme.vehiculo_desarme_id
                            if veh_id is not None:
                                remaining = PiezaDesarme.objects.filter(
                                    vehiculo_desarme_id=veh_id,
                                    empresa=documento.empresa,
                                    activo=True,
                                    cantidad__gt=0,
                                    estado_pieza=ESTADO_DISPONIBLE,
                                ).exists()
                                if not remaining:
                                    VehiculoDesarme.objects.filter(id=veh_id).update(
                                        estado_desarme="AGOTADO"
                                    )
                        except Exception:
                            log.exception(
                                "Error al actualizar estado del vehículo tras agotar piezas"
                            )

                    MovimientoInventario.objects.create(
                        empresa=documento.empresa,
                        tipo=tipo_mov,
                        origen_stock=MovimientoInventario.OrigenStock.DESARME,
                        pieza_desarme=linea.pieza_desarme,
                        documento=documento,
                        linea_repuesto=linea,
                        cantidad_delta=cantidad_actualizar,
                        saldo_resultante=saldo_nuevo,
                        costo_unitario=linea.costo_linea,
                        idempotency_key=idempotency_key,
                        metadata={
                            "inventory_ledger_version": InventoryLedgerService.HASH_VERSION,
                            "documento_tipo": documento.tipo,
                            "documento_estado": documento.estado,
                            "accion": accion,
                            "estado_anterior": estado_antes,
                            "estado_resultante": estado_nuevo,
                            "activo_anterior": activo_antes,
                            "activo_resultante": activo_nuevo,
                        },
                    )
                    movimientos.append({
                        "origen": ORIGEN_DESARME,
                        "pieza_desarme_id": pieza_id,
                        "nombre": linea.pieza_desarme.nombre,
                        "cantidad": abs(cantidad_actualizar),
                        "accion": "descontado" if cantidad_actualizar < 0 else "repuesto",
                        "saldo_anterior": saldo_antes,
                        "saldo_actual": saldo_nuevo,
                    })
                    log.info(
                        f"  ✅ DESARME {linea.pieza_desarme.nombre}: {abs(cantidad_actualizar)} u."
                    )
                else:
                    # ajustar: no ledger — mantener helper preexistente
                    InventoryService._actualizar_stock_desarme(linea.pieza_desarme, cantidad_actualizar)
                    movimientos.append({
                        "origen": ORIGEN_DESARME,
                        "pieza_desarme_id": linea.pieza_desarme.id,
                        "nombre": linea.pieza_desarme.nombre,
                        "cantidad": abs(cantidad_actualizar),
                        "accion": "descontado" if cantidad_actualizar < 0 else "repuesto",
                    })
                    log.info(
                        f"  ✅ DESARME {linea.pieza_desarme.nombre}: {abs(cantidad_actualizar)} u."
                    )
            # EXTERNO: no mover inventario

        return {
            "procesado": True,
            "movimientos": movimientos,
            "total_movimientos": len(movimientos),
        }

    @staticmethod
    def validar_stock_disponible(
        documento: Documento, snapshot_previo: Optional[list[dict]] = None
    ) -> List[str]:
        """
        Valida que hay stock suficiente para todas las líneas que mueven inventario
        (STOCK_BODEGA → Repuesto; DESARME → PiezaDesarme). EXTERNO no se valida.
        """
        errores = []
        if documento.tipo in InventoryService.TIPOS_SIN_STOCK:
            return errores

        reservas_previas = InventoryService._build_reserved_stock_map(snapshot_previo)
        lineas = documento.lineas_repuesto.select_related("repuesto", "pieza_desarme")
        for linea in lineas:
            if linea.origen_repuesto == ORIGEN_EXTERNO:
                continue
            if linea.origen_repuesto == ORIGEN_STOCK_BODEGA and linea.repuesto_id:
                if linea.repuesto.empresa_id != documento.empresa_id:
                    errores.append(
                        f"⚠️ Repuesto '{linea.repuesto.nombre}' no pertenece a tu empresa."
                    )
                    continue
                disponible = int(linea.repuesto.cantidad_stock or 0) + reservas_previas.get(
                    (ORIGEN_STOCK_BODEGA, int(linea.repuesto_id)), 0
                )
                if disponible < linea.cantidad:
                    errores.append(
                        f"❌ Stock insuficiente para '{linea.repuesto.nombre}'. "
                        f"Requerido: {linea.cantidad}, Disponible: {disponible}"
                    )
            elif linea.origen_repuesto == ORIGEN_DESARME and linea.pieza_desarme_id:
                pieza = linea.pieza_desarme
                reserva_previa = reservas_previas.get(
                    (ORIGEN_DESARME, int(linea.pieza_desarme_id)), 0
                )
                # Sin crédito de edición previa, la pieza debe estar DISPONIBLE
                if reserva_previa == 0 and pieza.estado_pieza != ESTADO_DISPONIBLE:
                    errores.append(
                        f"❌ Pieza '{pieza.nombre}' no está disponible "
                        f"(estado: {pieza.get_estado_pieza_display()})."
                    )
                    continue
                disponible = int(pieza.cantidad or 0) + reserva_previa
                if disponible < linea.cantidad:
                    errores.append(
                        f"❌ Stock insuficiente en pieza de desarme '{pieza.nombre}'. "
                        f"Requerido: {linea.cantidad}, Disponible: {disponible}"
                    )
        return errores

    @staticmethod
    @transaction.atomic
    def procesar_snapshot_movimiento(empresa, snapshot: Optional[list[dict]], accion: str):
        """
        Aplica movimientos desde una fotografia previa de lineas.
        Esto permite reponer o descontar stock aunque las lineas actuales
        hayan sido borradas y recreadas por completo.
        """
        if accion not in {"descontar", "reponer"}:
            raise ValueError(f"Accion de inventario no soportada: {accion}")

        factor = -1 if accion == "descontar" else 1
        for item in snapshot or []:
            cantidad = int(item.get("cantidad") or 0)
            if cantidad <= 0:
                continue

            origen = item.get("origen_repuesto")
            if origen == ORIGEN_STOCK_BODEGA and item.get("repuesto_id"):
                Repuesto.objects.filter(
                    id=item["repuesto_id"],
                    empresa=empresa,
                ).update(cantidad_stock=F("cantidad_stock") + (cantidad * factor))
            elif origen == ORIGEN_DESARME and item.get("pieza_desarme_id"):
                pieza = PiezaDesarme.objects.filter(id=item["pieza_desarme_id"]).first()
                if pieza:
                    InventoryService._actualizar_stock_desarme(pieza, cantidad * factor)

    @staticmethod
    def validar_y_procesar_emision(documento: Documento) -> tuple[bool, List[str]]:
        """
        Valida stock y procesa emisión en un solo paso.

        Args:
            documento: Documento a emitir

        Returns:
            tuple: (exito: bool, errores: List[str])
        """
        # 1. Validar stock disponible
        errores = InventoryService.validar_stock_disponible(documento)

        if errores:
            return False, errores

        # 2. Si pasa validación, descontar stock
        resultado = InventoryService.procesar_movimiento_stock(documento, "descontar")

        if not resultado.get("procesado"):
            errores.append(
                f"No se pudo procesar movimiento de stock: {resultado.get('razon', 'Desconocido')}"
            )
            return False, errores

        return True, []

    @staticmethod
    @transaction.atomic
    def procesar_edicion(documento_anterior: Documento, documento_nuevo: Documento):
        """
        Procesa cambios de stock cuando se edita un documento emitido.
        Por origen: STOCK_BODEGA (Repuesto) y DESARME (PiezaDesarme); EXTERNO no mueve.
        """
        if documento_anterior.estado != "EMITIDO":
            log.debug(f"[InventoryService] Documento {documento_anterior.numero} no estaba emitido")
            return
        if documento_nuevo.estado != "EMITIDO":
            InventoryService.procesar_movimiento_stock(documento_anterior, "reponer")
            return

        for linea in documento_nuevo.lineas_repuesto.select_related("repuesto", "pieza_desarme"):
            if linea.origen_repuesto == ORIGEN_EXTERNO:
                continue
            ant = (
                documento_anterior.lineas_repuesto.filter(id=linea.id)
                .select_related("repuesto", "pieza_desarme")
                .first()
            )
            if ant:
                cant_ant, rep_id_ant, pieza_id_ant, orig_ant = (
                    ant.cantidad,
                    ant.repuesto_id,
                    ant.pieza_desarme_id,
                    ant.origen_repuesto,
                )
                if (
                    orig_ant != linea.origen_repuesto
                    or rep_id_ant != linea.repuesto_id
                    or pieza_id_ant != linea.pieza_desarme_id
                ):
                    # Origen o referencia cambiaron: reponer anterior y descontar nuevo
                    if orig_ant == ORIGEN_STOCK_BODEGA and rep_id_ant:
                        InventoryService._actualizar_stock(ant.repuesto, cant_ant)
                    elif orig_ant == ORIGEN_DESARME and pieza_id_ant:
                        InventoryService._actualizar_stock_desarme(ant.pieza_desarme, cant_ant)
                    if linea.origen_repuesto == ORIGEN_STOCK_BODEGA and linea.repuesto_id:
                        InventoryService._actualizar_stock(linea.repuesto, -linea.cantidad)
                    elif linea.origen_repuesto == ORIGEN_DESARME and linea.pieza_desarme_id:
                        InventoryService._actualizar_stock_desarme(
                            linea.pieza_desarme, -linea.cantidad
                        )
                else:
                    diff = linea.cantidad - cant_ant
                    if diff == 0:
                        continue
                    if linea.origen_repuesto == ORIGEN_STOCK_BODEGA and linea.repuesto_id:
                        InventoryService._actualizar_stock(linea.repuesto, -diff)
                    elif linea.origen_repuesto == ORIGEN_DESARME and linea.pieza_desarme_id:
                        InventoryService._actualizar_stock_desarme(linea.pieza_desarme, -diff)
            else:
                if linea.origen_repuesto == ORIGEN_STOCK_BODEGA and linea.repuesto_id:
                    InventoryService._actualizar_stock(linea.repuesto, -linea.cantidad)
                elif linea.origen_repuesto == ORIGEN_DESARME and linea.pieza_desarme_id:
                    InventoryService._actualizar_stock_desarme(linea.pieza_desarme, -linea.cantidad)

        for linea_anterior in documento_anterior.lineas_repuesto.select_related(
            "repuesto", "pieza_desarme"
        ):
            if not documento_nuevo.lineas_repuesto.filter(id=linea_anterior.id).exists():
                if (
                    linea_anterior.origen_repuesto == ORIGEN_STOCK_BODEGA
                    and linea_anterior.repuesto_id
                ):
                    InventoryService._actualizar_stock(
                        linea_anterior.repuesto, linea_anterior.cantidad
                    )
                elif (
                    linea_anterior.origen_repuesto == ORIGEN_DESARME
                    and linea_anterior.pieza_desarme_id
                ):
                    InventoryService._actualizar_stock_desarme(
                        linea_anterior.pieza_desarme, linea_anterior.cantidad
                    )

    @staticmethod
    @transaction.atomic
    def procesar_edicion_con_ledger(
        snapshot_anterior: list,
        documento: Documento,
        operation_id: str,
    ) -> dict:
        """
        Registra en el ledger los cambios netos de stock de una edición de documento EMITIDO.

        Compara snapshot_anterior (estado previo de las líneas) con las líneas
        actuales del documento. Por cada recurso con delta neto ≠ 0:
          - aplica el delta al stock (Repuesto o PiezaDesarme)
          - crea un MovimientoInventario con tipo=EDICION

        operation_id (str UUID) permite distinguir ediciones concurrentes e
        idempotencia: si ya existe una clave para este operation_id, la operación
        se salta sin re-aplicar.

        Locking: SELECT FOR UPDATE sobre todos los Repuesto y PiezaDesarme
        afectados, ordenados por pk para evitar deadlocks.
        """
        from taller.models.movimiento_inventario import MovimientoInventario
        from taller.services.inventory_ledger_service import InventoryLedgerService

        if documento.tipo in InventoryService.TIPOS_SIN_STOCK:
            return {"procesado": False, "razon": "Tipo de documento no mueve stock"}

        # ── 1. Mapa anterior ─────────────────────────────────────────────────
        anterior_map: dict = defaultdict(int)
        for item in snapshot_anterior or []:
            origen = item.get("origen_repuesto")
            cantidad = int(item.get("cantidad") or 0)
            if cantidad <= 0:
                continue
            if origen == ORIGEN_STOCK_BODEGA and item.get("repuesto_id"):
                anterior_map[("B", int(item["repuesto_id"]))] += cantidad
            elif origen == ORIGEN_DESARME and item.get("pieza_desarme_id"):
                anterior_map[("D", int(item["pieza_desarme_id"]))] += cantidad

        # ── 2. Mapa nuevo ────────────────────────────────────────────────────
        nuevo_map: dict = defaultdict(int)
        lineas_nuevo = list(
            documento.lineas_repuesto.select_related("repuesto", "pieza_desarme").all()
        )
        for linea in lineas_nuevo:
            if linea.origen_repuesto == ORIGEN_EXTERNO:
                continue
            cant = int(linea.cantidad or 0)
            if cant <= 0:
                continue
            if linea.origen_repuesto == ORIGEN_STOCK_BODEGA and linea.repuesto_id:
                nuevo_map[("B", linea.repuesto_id)] += cant
            elif linea.origen_repuesto == ORIGEN_DESARME and linea.pieza_desarme_id:
                nuevo_map[("D", linea.pieza_desarme_id)] += cant

        # ── 3. Deltas netos (positivo = reponer al stock, negativo = consumir) ─
        all_keys = set(anterior_map.keys()) | set(nuevo_map.keys())
        delta_map = {
            k: anterior_map.get(k, 0) - nuevo_map.get(k, 0)
            for k in all_keys
            if anterior_map.get(k, 0) != nuevo_map.get(k, 0)
        }
        if not delta_map:
            log.info(
                f"[InventoryService] EDICION doc={documento.pk}: sin cambios netos, no se escribe ledger."
            )
            return {"procesado": True, "movimientos": [], "total_movimientos": 0}

        # ── 4. SELECT FOR UPDATE en orden pk ─────────────────────────────────
        bodega_ids = sorted(id_ for kind, id_ in delta_map if kind == "B")
        desarme_ids = sorted(id_ for kind, id_ in delta_map if kind == "D")

        saldo_bodega: dict = {}
        if bodega_ids:
            saldo_bodega = {
                r.pk: r.cantidad_stock
                for r in Repuesto.objects.select_for_update()
                .filter(id__in=bodega_ids, empresa=documento.empresa)
                .order_by("pk")
            }

        saldo_pieza: dict = {}
        estado_por_pieza_map: dict = {}
        activo_por_pieza_map: dict = {}
        if desarme_ids:
            locked_piezas = list(
                PiezaDesarme.objects.select_for_update()
                .filter(id__in=desarme_ids)
                .order_by("pk")
            )
            saldo_pieza = {p.pk: p.cantidad for p in locked_piezas}
            estado_por_pieza_map = {p.pk: p.estado_pieza for p in locked_piezas}
            activo_por_pieza_map = {p.pk: p.activo for p in locked_piezas}

        # ── 5. Helper: primera línea nueva para un recurso ───────────────────
        def _primera_linea(kind, resource_id):
            for ln in lineas_nuevo:
                if kind == "B" and ln.origen_repuesto == ORIGEN_STOCK_BODEGA and ln.repuesto_id == resource_id:
                    return ln
                if kind == "D" and ln.origen_repuesto == ORIGEN_DESARME and ln.pieza_desarme_id == resource_id:
                    return ln
            return None

        # ── 6. Loop: aplicar deltas + ledger ─────────────────────────────────
        movimientos: list = []
        for key in sorted(delta_map.keys()):
            kind, resource_id = key
            stock_delta = delta_map[key]

            if kind == "B":
                saldo_antes = saldo_bodega.get(resource_id, 0)

                # Idempotencia ANTES de cualquier modificación
                ikey = InventoryLedgerService.build_idempotency_key(
                    empresa_id=documento.empresa_id,
                    tipo=MovimientoInventario.TipoMovimiento.EDICION,
                    origen_stock=MovimientoInventario.OrigenStock.STOCK_BODEGA,
                    repuesto_id=resource_id,
                    pieza_desarme_id=None,
                    documento_id=documento.pk,
                    linea_repuesto_id=None,
                    cantidad_delta=stock_delta,
                    operation_id=operation_id,
                )
                if MovimientoInventario.objects.filter(idempotency_key=ikey).exists():
                    movimientos.append({"origen": ORIGEN_STOCK_BODEGA, "repuesto_id": resource_id, "delta": stock_delta, "idempotente": True})
                    log.info(f"  ♻️ EDICION BODEGA #{resource_id}: idempotente.")
                    continue

                saldo_nuevo = saldo_antes + stock_delta
                if saldo_nuevo < 0:
                    raise ValidationError(
                        f"Stock insuficiente en edición para repuesto #{resource_id}. "
                        f"Saldo: {saldo_antes}, delta: {stock_delta}."
                    )

                filas = Repuesto.objects.filter(
                    id=resource_id, empresa=documento.empresa
                ).update(cantidad_stock=F("cantidad_stock") + stock_delta)
                if filas == 0:
                    log.warning(f"[InventoryService] EDICION: no actualizó repuesto #{resource_id}")
                    continue
                saldo_bodega[resource_id] = saldo_nuevo

                primera_linea = _primera_linea("B", resource_id)
                MovimientoInventario.objects.create(
                    empresa=documento.empresa,
                    tipo=MovimientoInventario.TipoMovimiento.EDICION,
                    origen_stock=MovimientoInventario.OrigenStock.STOCK_BODEGA,
                    repuesto_id=resource_id,
                    pieza_desarme=None,
                    documento=documento,
                    linea_repuesto=primera_linea,
                    cantidad_delta=stock_delta,
                    saldo_resultante=saldo_nuevo,
                    costo_unitario=primera_linea.costo_linea if primera_linea else None,
                    idempotency_key=ikey,
                    metadata={
                        "inventory_ledger_version": InventoryLedgerService.HASH_VERSION,
                        "documento_tipo": documento.tipo,
                        "documento_estado": documento.estado,
                        "accion": "edicion",
                        "operation_id": operation_id,
                    },
                )
                movimientos.append({"origen": ORIGEN_STOCK_BODEGA, "repuesto_id": resource_id, "delta": stock_delta, "saldo_nuevo": saldo_nuevo})
                log.info(f"  ✅ EDICION BODEGA #{resource_id}: delta={stock_delta}, saldo={saldo_nuevo}")

            elif kind == "D":
                saldo_antes = saldo_pieza.get(resource_id, 0)
                estado_antes = estado_por_pieza_map.get(resource_id, ESTADO_DISPONIBLE)
                activo_antes = activo_por_pieza_map.get(resource_id, True)

                # Idempotencia ANTES de cualquier modificación
                ikey = InventoryLedgerService.build_idempotency_key(
                    empresa_id=documento.empresa_id,
                    tipo=MovimientoInventario.TipoMovimiento.EDICION,
                    origen_stock=MovimientoInventario.OrigenStock.DESARME,
                    repuesto_id=None,
                    pieza_desarme_id=resource_id,
                    documento_id=documento.pk,
                    linea_repuesto_id=None,
                    cantidad_delta=stock_delta,
                    operation_id=operation_id,
                )
                if MovimientoInventario.objects.filter(idempotency_key=ikey).exists():
                    movimientos.append({"origen": ORIGEN_DESARME, "pieza_id": resource_id, "delta": stock_delta, "idempotente": True})
                    log.info(f"  ♻️ EDICION DESARME #{resource_id}: idempotente.")
                    continue

                saldo_nuevo = saldo_antes + stock_delta
                if saldo_nuevo < 0:
                    raise ValidationError(
                        f"Stock insuficiente en edición para pieza #{resource_id}. "
                        f"Saldo: {saldo_antes}, delta: {stock_delta}."
                    )

                if saldo_nuevo <= 0:
                    estado_nuevo = ESTADO_VENDIDA
                    activo_nuevo = False
                elif estado_antes == ESTADO_VENDIDA and saldo_nuevo > 0:
                    estado_nuevo = ESTADO_DISPONIBLE
                    activo_nuevo = True
                else:
                    estado_nuevo = estado_antes
                    activo_nuevo = activo_antes

                filas = PiezaDesarme.objects.filter(
                    id=resource_id, empresa=documento.empresa
                ).update(
                    cantidad=F("cantidad") + stock_delta,
                    estado_pieza=estado_nuevo,
                    activo=activo_nuevo,
                )
                if filas == 0:
                    log.warning(f"[InventoryService] EDICION: no actualizó pieza #{resource_id}")
                    continue
                saldo_pieza[resource_id] = saldo_nuevo
                estado_por_pieza_map[resource_id] = estado_nuevo
                activo_por_pieza_map[resource_id] = activo_nuevo

                if saldo_nuevo <= 0:
                    try:
                        pieza_info = PiezaDesarme.objects.filter(id=resource_id).values("vehiculo_desarme_id").first()
                        veh_id = pieza_info["vehiculo_desarme_id"] if pieza_info else None
                        if veh_id:
                            remaining = PiezaDesarme.objects.filter(
                                vehiculo_desarme_id=veh_id,
                                empresa=documento.empresa,
                                activo=True,
                                cantidad__gt=0,
                                estado_pieza=ESTADO_DISPONIBLE,
                            ).exists()
                            if not remaining:
                                VehiculoDesarme.objects.filter(id=veh_id).update(estado_desarme="AGOTADO")
                    except Exception:
                        log.exception("Error al actualizar estado del vehículo en edición")

                primera_linea = _primera_linea("D", resource_id)
                MovimientoInventario.objects.create(
                    empresa=documento.empresa,
                    tipo=MovimientoInventario.TipoMovimiento.EDICION,
                    origen_stock=MovimientoInventario.OrigenStock.DESARME,
                    repuesto=None,
                    pieza_desarme_id=resource_id,
                    documento=documento,
                    linea_repuesto=primera_linea,
                    cantidad_delta=stock_delta,
                    saldo_resultante=saldo_nuevo,
                    costo_unitario=primera_linea.costo_linea if primera_linea else None,
                    idempotency_key=ikey,
                    metadata={
                        "inventory_ledger_version": InventoryLedgerService.HASH_VERSION,
                        "documento_tipo": documento.tipo,
                        "documento_estado": documento.estado,
                        "accion": "edicion",
                        "operation_id": operation_id,
                        "estado_anterior": estado_antes,
                        "estado_resultante": estado_nuevo,
                        "activo_anterior": activo_antes,
                        "activo_resultante": activo_nuevo,
                    },
                )
                movimientos.append({"origen": ORIGEN_DESARME, "pieza_id": resource_id, "delta": stock_delta, "saldo_nuevo": saldo_nuevo})
                log.info(f"  ✅ EDICION DESARME #{resource_id}: delta={stock_delta}, saldo={saldo_nuevo}")

        return {
            "procesado": True,
            "movimientos": movimientos,
            "total_movimientos": len(movimientos),
        }

    @staticmethod
    @transaction.atomic
    def _actualizar_stock(repuesto: Repuesto, cantidad: int):
        """Actualiza stock de un repuesto (STOCK_BODEGA). cantidad: + reponer, - descontar."""
        Repuesto.objects.filter(id=repuesto.id).update(
            cantidad_stock=F("cantidad_stock") + cantidad
        )
        repuesto.refresh_from_db()

    @staticmethod
    @transaction.atomic
    def _actualizar_stock_desarme(pieza: "PiezaDesarme", cantidad: int):
        """
        Actualiza cantidad de PiezaDesarme. cantidad: + reponer, - descontar.
        Cuando cantidad llega a 0: estado_pieza=VENDIDA, activo=False.
        Cuando se repone y pasa de 0 a >0 desde VENDIDA: estado_pieza=DISPONIBLE, activo=True.
        """
        PiezaDesarme.objects.filter(id=pieza.id).update(cantidad=F("cantidad") + cantidad)
        pieza.refresh_from_db()

        if pieza.cantidad <= 0:
            PiezaDesarme.objects.filter(id=pieza.id).update(
                estado_pieza=ESTADO_VENDIDA, activo=False
            )
            pieza.refresh_from_db()
            # Si el vehículo asociado no tiene más piezas vendibles reales, marcar como AGOTADO
            # Piezas vendibles reales: activo=True, cantidad>0, estado_pieza in [DISPONIBLE, RESERVADA]
            try:
                veh_id = getattr(pieza, "vehiculo_desarme_id", None)
                if veh_id is not None:
                    remaining = PiezaDesarme.objects.filter(
                        vehiculo_desarme_id=veh_id,
                        empresa=pieza.empresa,
                        activo=True,
                        cantidad__gt=0,
                        estado_pieza=ESTADO_DISPONIBLE,
                    ).exists()
                    if not remaining:
                        VehiculoDesarme.objects.filter(id=veh_id).update(estado_desarme="AGOTADO")
            except Exception:
                log.exception("Error al actualizar estado del vehículo tras agotar piezas")
        elif pieza.estado_pieza == ESTADO_VENDIDA and pieza.cantidad > 0:
            # Reposición desde cero: volver a disponible
            PiezaDesarme.objects.filter(id=pieza.id).update(
                estado_pieza=ESTADO_DISPONIBLE, activo=True
            )
            pieza.refresh_from_db()
