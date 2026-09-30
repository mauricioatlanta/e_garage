from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, ORIGEN_STOCK_BODEGA
from taller.models.repuesto import Repuesto
from taller.services.inventory_service import InventoryService


class PartsPOSService:
    PAYMENT_METHODS = {"efectivo", "tarjeta", "transferencia"}

    @staticmethod
    def search(empresa, query: str, limit: int = 12):
        return (
            Repuesto.objects.filter(empresa=empresa)
            .buscar_mostrador(query)
            .select_related("categoria")
            .order_by("nombre", "part_number")[:limit]
        )

    @staticmethod
    def serialize_part(repuesto: Repuesto) -> dict:
        return {
            "id": repuesto.pk,
            "part_number": repuesto.part_number or "",
            "codigo_oem": repuesto.codigo_oem or "",
            "nombre": repuesto.nombre,
            "precio_venta": str(repuesto.precio_venta),
            "stock": repuesto.cantidad_stock,
            "ubicacion": repuesto.ubicacion or "",
            "medida": repuesto.medida_completa,
            "marca_neumatico": repuesto.marca_neumatico,
            "modelo_neumatico": repuesto.modelo_neumatico,
        }

    @staticmethod
    @transaction.atomic
    def create_sale(empresa, user, payload: dict) -> Documento:
        items = payload.get("items") or []
        if not items:
            raise ValidationError("El carrito no tiene productos.")

        payment_method = (payload.get("payment_method") or "efectivo").strip().lower()
        if payment_method not in PartsPOSService.PAYMENT_METHODS:
            raise ValidationError("Método de pago inválido.")

        cliente = PartsPOSService._resolve_cliente(empresa, payload.get("cliente_id"))
        repuestos = PartsPOSService._lock_repuestos(empresa, items)

        documento = Documento.objects.create(
            empresa=empresa,
            tipo="PTS",
            estado="EMITIDO",
            cliente=cliente,
            metodo_pago=payment_method,
            estado_pago="PAGADO",
            pagado=True,
            apply_vat=True,
            observaciones=(payload.get("observaciones") or "Venta rápida POS").strip(),
            created_by=user if getattr(user, "is_authenticated", False) else None,
        )

        for item in items:
            repuesto_id = int(item.get("repuesto_id") or item.get("id") or 0)
            repuesto = repuestos.get(repuesto_id)
            if repuesto is None:
                raise ValidationError("El carrito contiene un repuesto inválido.")

            cantidad = int(item.get("cantidad") or 1)
            if cantidad <= 0:
                raise ValidationError("La cantidad debe ser mayor a cero.")

            precio_unitario = PartsPOSService._decimal_or_default(
                item.get("precio_unitario"),
                repuesto.precio_venta,
            )

            LineaRepuesto.objects.create(
                documento=documento,
                repuesto=repuesto,
                codigo=repuesto.part_number or repuesto.codigo_oem or str(repuesto.pk),
                nombre=repuesto.nombre,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                descuento=Decimal("0.00"),
                origen_repuesto=ORIGEN_STOCK_BODEGA,
            )

        errores = InventoryService.validar_stock_disponible(documento)
        if errores:
            raise ValidationError(errores)

        resultado = InventoryService.procesar_movimiento_stock(documento, "descontar")
        if not resultado.get("procesado"):
            raise ValidationError(resultado.get("razon") or "No se pudo descontar stock.")

        documento.recalcular_totales(save=True)
        documento.monto_pagado = documento.total
        documento.save(update_fields=["monto_pagado"])
        return documento

    @staticmethod
    def _resolve_cliente(empresa, cliente_id):
        if cliente_id:
            cliente = Cliente.objects.filter(empresa=empresa, pk=cliente_id).first()
            if cliente:
                return cliente
        return Cliente.get_or_create_mostrador(empresa)

    @staticmethod
    def _lock_repuestos(empresa, items):
        ids = {
            int(item.get("repuesto_id") or item.get("id") or 0)
            for item in items
            if item.get("repuesto_id") or item.get("id")
        }
        if not ids:
            raise ValidationError("El carrito no contiene repuestos válidos.")
        return {
            repuesto.pk: repuesto
            for repuesto in Repuesto.objects.select_for_update()
            .filter(empresa=empresa, pk__in=ids)
            .order_by("pk")
        }

    @staticmethod
    def _decimal_or_default(value, default):
        if value in (None, ""):
            return default
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return default
