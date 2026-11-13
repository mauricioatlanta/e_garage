from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db import transaction

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio, ORIGEN_STOCK_BODEGA
from taller.models.repuesto import Repuesto
from taller.services.inventory_service import InventoryService


class PartsPOSService:
    PAYMENT_METHODS = {"efectivo", "tarjeta", "transferencia"}

    @staticmethod
    def search(empresa, query: str, limit: int = 12, categoria_filtro: str = ""):
        q = (query or "").strip()
        cat = (categoria_filtro or "").strip()
        # Sin texto ni filtro: no mostrar todo de golpe (comportamiento actual)
        if not q and not cat:
            return Repuesto.objects.filter(empresa=empresa).none()
        if q:
            qs = Repuesto.objects.filter(empresa=empresa).buscar_mostrador(q).select_related("categoria")
        else:
            qs = Repuesto.objects.filter(empresa=empresa).select_related("categoria")
        # Filtro inteligente Vulcanización: no esconder los 129 sin categoría
        # Solo usa campos reales: nombre, part_number, sku, codigo_oem, proveedor, categoria__nombre
        if cat == "Neumáticos":
            qs = qs.filter(
                Q(categoria__nombre__icontains="Neum") |
                Q(nombre__icontains="neum") |
                Q(nombre__icontains="205/") | Q(nombre__icontains="195/") |
                Q(nombre__icontains="185/") | Q(nombre__icontains="175/") |
                Q(part_number__icontains="205/") | Q(part_number__icontains="195/")
            )
        elif cat == "Rines":
            qs = qs.filter(
                Q(categoria__nombre__icontains="Rin") |
                Q(nombre__icontains="rin") | Q(nombre__icontains="llanta") |
                Q(nombre__icontains="aro")
            )
        elif cat == "Válvulas":
            qs = qs.filter(
                Q(categoria__nombre__icontains="Válvula") | Q(categoria__nombre__icontains="Valvula") |
                Q(nombre__icontains="válvula") | Q(nombre__icontains="valvula")
            )
        elif cat == "Accesorios":
            qs = qs.filter(
                Q(categoria__nombre__icontains="Accesorio") |
                Q(nombre__icontains="gata") | Q(nombre__icontains="cadena") |
                Q(nombre__icontains="inflador") | Q(nombre__icontains="tapa")
            )
        elif cat:
            # Fallback genérico Casa de Repuestos / Taller: Motor, Frenos, Suspensión, etc.
            # Solo campo real categoria__nombre, sin inventar. Si la categoría no existe en DB, da 0, no error.
            qs = qs.filter(Q(categoria__nombre__icontains=cat))
        # Todos / sin cat: sin filtro extra, muestra lo buscado incluidos sin categoría
        return qs.order_by("nombre", "part_number")[:limit]

    @staticmethod
    def search_servicios(empresa, query: str, rubro: str = "TIRE", limit: int = 12):
        """Servicios de mesón por rubro, desde CatalogoServicio (sin precio, precio manual en POS)."""
        from taller.servicios.models import CatalogoServicio
        q = (query or "").strip()
        qs = CatalogoServicio.objects.filter(rubro=rubro, activo=True).order_by("orden", "nombre")
        if q:
            qs = qs.filter(nombre__icontains=q)
        return qs[:limit]

    @staticmethod
    def serialize_servicio(catalogo) -> dict:
        return {"id": catalogo.pk, "nombre": catalogo.nombre, "tipo": "servicio", "precio": None}  # Sin precio fijo: varía por complejidad del auto, se ingresa manual en POS

    @staticmethod
    def serialize_part(repuesto: Repuesto) -> dict:
        return {
            "id": repuesto.pk,
            "part_number": repuesto.part_number or "",
            "codigo_oem": repuesto.codigo_oem or "",
            "nombre": repuesto.nombre,
            "precio_venta": str(repuesto.precio_venta),
            "stock": repuesto.cantidad_stock,
            "sku": getattr(repuesto, "sku", "") or "",
            "ubicacion": getattr(repuesto, "ubicacion", "") or "",
            "medida": getattr(repuesto, "medida_completa", "") or "",
            "marca_neumatico": getattr(repuesto, "marca_neumatico", "") or "",
            "modelo_neumatico": getattr(repuesto, "modelo_neumatico", "") or "",
            "categoria": repuesto.categoria.nombre if getattr(repuesto, "categoria", None) else "",
        }

    @staticmethod
    @transaction.atomic
    def create_sale(empresa, user, payload: dict) -> Documento:
        items = payload.get("items") or []
        servicios = payload.get("servicios") or []
        if not items and not servicios:
            raise ValidationError("El carrito está vacío. Agrega un repuesto o un servicio.")

        payment_method = (payload.get("payment_method") or "efectivo").strip().lower()
        if payment_method not in PartsPOSService.PAYMENT_METHODS:
            raise ValidationError("Método de pago inválido.")

        cliente = PartsPOSService._resolve_cliente(
            empresa,
            payload.get("cliente_id"),
            nombre=payload.get("cliente_nombre"),
            telefono=payload.get("cliente_telefono"),
            user=user,
        )
        repuestos = PartsPOSService._lock_repuestos(empresa, items)
        apply_vat = PartsPOSService._as_bool(payload.get("apply_vat"), default=True)

        documento = Documento.objects.create(
            empresa=empresa,
            tipo="PTS",
            estado="EMITIDO",
            cliente=cliente,
            metodo_pago=payment_method,
            estado_pago="PAGADO",
            pagado=True,
            apply_vat=apply_vat,
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

        # Servicios de mesón: sin stock, precio manual en POS, sin FK obligatoria
        for srv in servicios:
            nombre_srv = str(srv.get("nombre") or "").strip()
            if not nombre_srv:
                continue
            cantidad_srv = int(srv.get("cantidad") or 1)
            if cantidad_srv <= 0:
                raise ValidationError("La cantidad del servicio debe ser mayor a cero.")
            precio_srv = PartsPOSService._decimal_or_default(srv.get("precio_unitario"), Decimal("0.00"))
            LineaServicio.objects.create(
                documento=documento,
                servicio=None,
                service=None,
                nombre=nombre_srv,
                cantidad=cantidad_srv,
                precio_unitario=precio_srv,
                descuento=Decimal("0.00"),
            )

        # Solo validar/descontar stock si hay repuestos. Si es solo servicios, no toca inventario.
        if not items:
            documento.recalcular_totales(save=True)
            documento.monto_pagado = documento.total
            documento.save(update_fields=["monto_pagado"])
            return documento

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
    def _resolve_cliente(empresa, cliente_id, nombre="", telefono="", user=None):
        if cliente_id:
            cliente = Cliente.objects.filter(empresa=empresa, pk=cliente_id).first()
            if cliente:
                return cliente

        telefono = str(telefono or "").strip()
        nombre = str(nombre or "").strip()
        if telefono:
            cliente = Cliente.objects.filter(empresa=empresa, telefono=telefono).first()
            if cliente:
                return cliente
            if not nombre:
                raise ValidationError("Para registrar un cliente nuevo debes indicar su nombre.")
            cliente, _ = Cliente.objects.get_or_create(
                empresa=empresa,
                telefono=telefono,
                defaults={"nombre": nombre, "created_by": user},
            )
            return cliente
        return Cliente.get_or_create_mostrador(empresa)

    @staticmethod
    def _as_bool(value, default=False):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on", "si"}

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
