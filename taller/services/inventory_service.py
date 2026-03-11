"""
Servicio de gestión de inventario (Inventory Service)

Maneja la lógica de movimientos de stock asegurando integridad.
Implementa las reglas de negocio:
- Los Presupuestos (PRES) NUNCA mueven stock
- Las Órdenes de Trabajo (OT) y Facturas (FAC) SÍ mueven stock
- Las ediciones deben calcular diferencia correctamente
- Las anulaciones deben devolver el stock
"""

import logging
from decimal import Decimal
from typing import List, Optional

from django.db import transaction
from django.db.models import F

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto
from taller.models.repuesto import Repuesto

log = logging.getLogger(__name__)


class InventoryService:
    """
    Maneja la lógica de movimientos de stock asegurando integridad.

    Reglas de Negocio:
    - Los Presupuestos (PRES) NUNCA mueven stock
    - Las Órdenes de Trabajo (OT) y Facturas (FAC) SÍ mueven stock
    - Solo se procesan líneas con repuesto vinculado (repuesto_id no nulo)
    - Solo repuestos con tipo_origen in (stock, desarme) mueven inventario; tipo_origen=direct no descuenta stock
    - Usa F() expressions para evitar race conditions
    """

    # Tipos de documento que NO mueven stock
    TIPOS_SIN_STOCK = ["PRES"]  # Presupuestos

    # Tipos de documento que SÍ mueven stock
    TIPOS_CON_STOCK = ["OT", "FAC"]  # Orden de Trabajo, Factura/Boleta

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
        """
        # Regla de Negocio: Los Presupuestos NUNCA mueven stock
        if documento.tipo in InventoryService.TIPOS_SIN_STOCK:
            log.debug(
                f"[InventoryService] Documento {documento.numero} es tipo {documento.tipo}, no mueve stock"
            )
            return {"procesado": False, "razon": "Tipo de documento no mueve stock"}

        # Solo procesar líneas con repuesto vinculado que controlan stock
        # Excluye tipo_origen direct/directo y controlar_stock=False
        lineas = (
            documento.lineas_repuesto.filter(repuesto__isnull=False)
            .exclude(repuesto__tipo_origen__in=("direct", "directo"))
            .exclude(repuesto__controlar_stock=False)
            .select_related("repuesto")
        )

        if not lineas.exists():
            log.debug(
                f"[InventoryService] Documento {documento.numero} no tiene líneas con repuesto vinculado"
            )
            return {"procesado": False, "razon": "No hay líneas con repuesto vinculado"}

        multiplier = -1 if accion == "descontar" else 1 if accion == "reponer" else 0

        # Para ajustar (ediciones), calcular diferencia
        if accion == "ajustar" and cantidades_anteriores:
            multiplier = 1  # Usaremos diferencia directa

        log.info(
            f"📦 Inventario: Procesando {accion} para Doc {documento.numero} (Tipo: {documento.tipo})"
        )

        resultados = []
        movimientos = []

        for linea in lineas:
            repuesto = linea.repuesto

            # Determinar cantidad a mover según acción
            if accion == "ajustar" and cantidades_anteriores:
                # Edición: calcular diferencia
                cantidad_anterior = cantidades_anteriores.get(linea.id, 0)
                diferencia = linea.cantidad - cantidad_anterior

                if diferencia == 0:
                    continue  # No hay cambio, saltar

                cantidad_actualizar = -diferencia  # Negativo para descontar, positivo para reponer
            else:
                # Creación o anulación: usar cantidad de la línea con multiplicador
                cantidad_actualizar = -linea.cantidad if multiplier < 0 else linea.cantidad

            # Obtener stock anterior ANTES de actualizar (para logging)
            stock_anterior = repuesto.cantidad_stock

            # Actualizar stock en la base de datos (atómico)
            # Usar F() expression para evitar race conditions
            filas_actualizadas = Repuesto.objects.filter(
                id=repuesto.id,
                empresa=documento.empresa,  # 🔒 Multi-tenant: asegurar empresa correcta
            ).update(cantidad_stock=F("cantidad_stock") + cantidad_actualizar)

            # Verificar que se actualizó correctamente
            if filas_actualizadas == 0:
                log.warning(
                    f"[InventoryService] No se actualizó stock para repuesto {repuesto.id} (puede no existir o no pertenecer a la empresa)"
                )
                continue

            # Refrescar desde BD para obtener stock actualizado DESPUÉS de la actualización
            repuesto.refresh_from_db()

            cantidad_movida = abs(cantidad_actualizar)
            accion_real = "descontado" if cantidad_actualizar < 0 else "repuesto"

            movimientos.append(
                {
                    "repuesto_id": repuesto.id,
                    "repuesto_nombre": repuesto.nombre,
                    "cantidad": cantidad_movida,
                    "accion": accion_real,
                    "stock_anterior": stock_anterior,
                    "stock_actual": repuesto.cantidad_stock,
                }
            )

            log.info(
                f"  ✅ {repuesto.nombre}: "
                f"{accion_real.capitalize()} "
                f"{cantidad_movida} unidades. "
                f"Stock: {stock_anterior} → {repuesto.cantidad_stock}"
            )

        return {
            "procesado": True,
            "movimientos": movimientos,
            "total_movimientos": len(movimientos),
        }

    @staticmethod
    def validar_stock_disponible(documento: Documento) -> List[str]:
        """
        Valida que hay stock suficiente para todos los repuestos del documento.

        Útil antes de cambiar estado a 'EMITIDO'.

        Args:
            documento: Documento a validar

        Returns:
            List[str]: Lista de errores (vacía si todo está bien)
        """
        errores = []

        # Presupuestos no necesitan validación de stock
        if documento.tipo in InventoryService.TIPOS_SIN_STOCK:
            return errores

        # Solo validar stock en repuestos que controlan inventario
        lineas = (
            documento.lineas_repuesto.filter(repuesto__isnull=False)
            .exclude(repuesto__tipo_origen__in=("direct", "directo"))
            .exclude(repuesto__controlar_stock=False)
            .select_related("repuesto")
        )

        for linea in lineas:
            repuesto = linea.repuesto

            # Validar que el repuesto pertenece a la misma empresa (multi-tenant)
            if repuesto.empresa_id != documento.empresa_id:
                errores.append(f"⚠️ Repuesto '{repuesto.nombre}' no pertenece a tu empresa.")
                continue

            stock_disponible = repuesto.cantidad_stock
            cantidad_requerida = linea.cantidad

            if stock_disponible < cantidad_requerida:
                errores.append(
                    f"❌ Stock insuficiente para '{repuesto.nombre}'. "
                    f"Requerido: {cantidad_requerida}, Disponible: {stock_disponible}"
                )

        return errores

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

        Maneja:
        - Cambios de cantidad: ajusta diferencia
        - Líneas agregadas: descuenta nueva cantidad
        - Líneas eliminadas: repone cantidad eliminada

        Args:
            documento_anterior: Versión anterior del documento
            documento_nuevo: Versión nueva del documento
        """
        # Solo procesar si el documento estaba emitido
        if documento_anterior.estado != "EMITIDO":
            log.debug(
                f"[InventoryService] Documento {documento_anterior.numero} no estaba emitido, no hay stock que ajustar"
            )
            return

        # Si el nuevo documento ya no está emitido, devolver todo el stock
        if documento_nuevo.estado != "EMITIDO":
            InventoryService.procesar_movimiento_stock(documento_anterior, "reponer")
            return

        # Construir mapa de cantidades anteriores
        cantidades_anteriores = {
            linea.id: linea.cantidad
            for linea in documento_anterior.lineas_repuesto.filter(repuesto__isnull=False)
        }

        # Construir mapa de cantidades nuevas
        cantidades_nuevas = {
            linea.repuesto_id: linea.cantidad
            for linea in documento_nuevo.lineas_repuesto.filter(repuesto__isnull=False)
        }

        # Procesar cada línea nueva
        for linea in documento_nuevo.lineas_repuesto.filter(repuesto__isnull=False):
            repuesto_id = linea.repuesto_id
            cantidad_nueva = linea.cantidad

            # Buscar línea anterior con mismo repuesto
            linea_anterior = documento_anterior.lineas_repuesto.filter(
                repuesto_id=repuesto_id
            ).first()

            if linea_anterior:
                # Línea existente: calcular diferencia
                cantidad_anterior = linea_anterior.cantidad
                diferencia = cantidad_nueva - cantidad_anterior

                if diferencia > 0:
                    # Aumentó cantidad: descontar diferencia
                    log.info(
                        f"[InventoryService] Línea editada: {linea.repuesto.nombre} {cantidad_anterior} → {cantidad_nueva} (+{diferencia})"
                    )
                    InventoryService._actualizar_stock(linea.repuesto, -diferencia)
                elif diferencia < 0:
                    # Disminuyó cantidad: reponer diferencia
                    log.info(
                        f"[InventoryService] Línea editada: {linea.repuesto.nombre} {cantidad_anterior} → {cantidad_nueva} ({diferencia})"
                    )
                    InventoryService._actualizar_stock(linea.repuesto, abs(diferencia))
                # Si diferencia == 0, no hacer nada
            else:
                # Nueva línea: descontar cantidad nueva
                log.info(
                    f"[InventoryService] Nueva línea agregada: {linea.repuesto.nombre} x{cantidad_nueva}"
                )
                InventoryService._actualizar_stock(linea.repuesto, -cantidad_nueva)

        # Procesar líneas eliminadas: reponer stock
        for linea_anterior in documento_anterior.lineas_repuesto.filter(repuesto__isnull=False):
            # Verificar si la línea ya no existe en el documento nuevo
            existe_nueva = documento_nuevo.lineas_repuesto.filter(
                repuesto_id=linea_anterior.repuesto_id, id=linea_anterior.id  # Mismo ID
            ).exists()

            if not existe_nueva:
                # Línea eliminada: reponer stock
                log.info(
                    f"[InventoryService] Línea eliminada: {linea_anterior.repuesto.nombre} x{linea_anterior.cantidad}"
                )
                InventoryService._actualizar_stock(linea_anterior.repuesto, linea_anterior.cantidad)

    @staticmethod
    @transaction.atomic
    def _actualizar_stock(repuesto: Repuesto, cantidad: int):
        """
        Actualiza stock de un repuesto usando F() expression (atómico).

        Args:
            repuesto: Repuesto a actualizar
            cantidad: Cantidad a agregar (positivo) o descontar (negativo)

        Example:
            _actualizar_stock(repuesto, -5)  # Descontar 5 unidades
            _actualizar_stock(repuesto, 3)   # Agregar 3 unidades
        """
        Repuesto.objects.filter(id=repuesto.id).update(
            cantidad_stock=F("cantidad_stock") + cantidad
        )
        repuesto.refresh_from_db()
