from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import DecimalField, ExpressionWrapper, F, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.utils.translation import gettext_lazy as _  # 👈 Para traducciones

from taller.models.clientes import Cliente
from taller.models.mixins import AuditMixin
from taller.models.vehiculos import Vehiculo

from .utils_monedas import money_quantize


class Documento(AuditMixin, models.Model):
    empresa = models.ForeignKey(
        "taller.Empresa", on_delete=models.CASCADE, related_name="documentos"
    )
    tecnico_responsable = models.ForeignKey(
        "taller.Tecnico",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="documentos_responsables",
    )
    CONTEXT_CHOICES = [
        ("workshop", _("Workshop")),
        ("parts", _("Parts")),
        ("mixed", _("Mixed")),
    ]
    context = models.CharField(
        max_length=16,
        choices=CONTEXT_CHOICES,
        default="workshop",
        db_index=True,
        help_text=_("Workshop=OT/servicios, Parts=repuestos sin vehículo, Mixed=factura con ambos"),
    )
    tipo = models.CharField(
        max_length=4,
        choices=[
            ("OT", _("Orden de Trabajo")),
            ("PRES", _("Presupuesto")),
            ("FAC", _("Factura/Boleta")),
            # ("REC", _("Recibo/Boleta (LEGACY)")),  # Legacy, no mostrar en forms
            # ("BOL", _("Boleta (LEGACY)")),   # Legacy, no mostrar en forms
        ],
        db_index=True,
    )
    numero = models.CharField(max_length=32, blank=True, default="", db_index=True)
    # numero_documento_db removido - era duplicado de numero
    # correlativo removido - no se actualizaba automáticamente
    # estado del documento (borrador/emitido/anulado, etc.)
    ESTADOS_DOC = (
        ("BORRADOR", "Borrador"),
        ("EMITIDO", "Emitido"),
        ("ANULADO", "Anulado"),
    )
    estado = models.CharField(
        max_length=12, choices=ESTADOS_DOC, default="EMITIDO", blank=True, db_index=True
    )
    fecha_emision = models.DateField(default=timezone.now, editable=True, db_index=True)
    cliente = models.ForeignKey(
        Cliente, on_delete=models.PROTECT, related_name="documentos", db_index=True
    )
    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos",
    )
    moneda = models.CharField(max_length=3, default="CLP")
    country = models.CharField(max_length=2, default="CL")
    neto_repuestos = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    neto_servicios = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    neto_otros_servicios = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    descuento = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    tax_rate_applied = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    # Columnas legacy para compatibilidad con bases antiguas / frontend
    legacy_total_repuestos = models.DecimalField(
        db_column="total_repuestos",
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    legacy_total_servicios = models.DecimalField(
        db_column="total_servicios",
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    legacy_total_otros = models.DecimalField(
        db_column="total_otros",
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    legacy_iva = models.DecimalField(
        db_column="iva",
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    legacy_total_general = models.DecimalField(
        db_column="total_general",
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    # Opcional: estado de pago (choices para select en formulario)
    PAYMENT_STATUS = [
        ("unpaid", _("Unpaid")),
        ("pending", _("Pending")),
        ("partial", _("Partial")),
        ("paid", _("Paid")),
        ("refunded", _("Refunded")),
        ("canceled", _("Canceled")),
    ]
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS, blank=True, default="pending"
    )

    created_at = models.DateTimeField(default=timezone.now)

    # Campos nuevos para tracking de pagos y observaciones
    estado_pago = models.CharField(
        max_length=10,
        choices=[
            ("PAGADO", _("Pagado")),
            ("NO_PAGADO", _("No Pagado")),
            ("PARCIAL", _("Pago Parcial")),
        ],
        default="NO_PAGADO",
        db_index=True,
        help_text=_("Estado del pago del documento"),
    )
    pagado = models.BooleanField(
        default=False, help_text=_("Indica si el documento está pagado completamente")
    )
    apply_vat = models.BooleanField(default=True, help_text=_("Aplicar IVA al documento"))
    kilometraje = models.PositiveIntegerField(
        null=True, blank=True, help_text=_("Kilometraje del vehículo")
    )
    millas = models.PositiveIntegerField(
        null=True, blank=True, help_text=_("Millaje del vehículo (solo para USA)")
    )
    observaciones = models.TextField(
        blank=True, null=True, help_text=_("Notas u observaciones sobre el documento")
    )

    # Campos de forma de pago
    metodo_pago = models.CharField(
        max_length=20,
        choices=[
            ("efectivo", _("Efectivo")),
            ("transferencia", _("Transferencia")),
            ("tarjeta", _("Tarjeta")),
            ("cheque", _("Cheque")),
        ],
        blank=True,
        null=True,
        help_text=_("Método de pago utilizado"),
    )
    ult4 = models.CharField(
        max_length=4,
        blank=True,
        null=True,
        help_text=_("Últimos 4 dígitos de tarjeta (si aplica)"),
    )
    monto_pagado = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Monto efectivamente pagado"),
    )
    saldo_pendiente = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text=_("Saldo pendiente de pago"),
    )
    fecha_pago = models.DateTimeField(blank=True, null=True, help_text=_("Fecha y hora del pago"))
    nota_pago = models.TextField(
        blank=True, null=True, help_text=_("Notas adicionales sobre el pago")
    )

    # --------- Helpers internos ---------
    def vat_percent(self) -> float:
        """
        Tasa de impuesto por país usando configuración centralizada.

        Returns:
            float: Tasa de impuesto (ej: 19.0 para 19%)
        """
        from taller.utils.country_config import get_config_from_documento

        config = get_config_from_documento(self)
        return config["tax_rate"]

    def _decimals(self):
        """
        Decimales por país/moneda usando configuración centralizada.

        Returns:
            int: Número de decimales (0 o 2)
        """
        from taller.utils.country_config import get_config_from_documento

        config = get_config_from_documento(self)
        return config["decimals"]

    def _q(self, value, decs=None):
        """
        Quantize con HALF_UP según decimales de la empresa.
        """
        if value is None:
            value = Decimal("0")
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        if decs is None:
            decs = self._decimals()
        q = Decimal("1") if decs == 0 else Decimal("0." + "0" * (decs - 1) + "1")
        return value.quantize(q, rounding=ROUND_HALF_UP)

    def _resolve_tax_rate(self):
        """
        Resuelve la tasa: si el campo ya viene seteado, la usa.
        Si no, obtiene la tasa de ConfiguracionEmpresa o usa valores por defecto.
        """
        if getattr(self, "tax_rate_applied", None) not in (None, ""):
            try:
                return Decimal(str(self.tax_rate_applied))
            except Exception:
                pass

        # Intentar obtener tasa de ConfiguracionEmpresa
        try:
            from taller.models.empresa import ConfiguracionEmpresa

            config = ConfiguracionEmpresa.objects.filter(empresa=self.empresa).first()
            if config and hasattr(config, "tasa_iva") and config.tasa_iva is not None:
                return Decimal(str(config.tasa_iva))
        except (ImportError, AttributeError, Exception):
            pass

        # Valores por defecto por país usando configuración centralizada
        from taller.utils.country_config import get_config_from_documento

        config = get_config_from_documento(self)
        return Decimal(str(config["tax_rate"]))

    def _sum_repuesto(self):
        # Calcula cantidad*precio_unitario - descuento línea
        qs = getattr(self, "lineas_repuesto", None)
        if not qs:
            return Decimal("0")

        # Calcular subtotal con descuento en porcentaje
        expr = ExpressionWrapper(
            F("cantidad") * F("precio_unitario") * (1 - F("descuento") / 100),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
        total = qs.aggregate(s=Sum(expr)).get("s") or Decimal("0")
        return Decimal(total)

    def _sum_servicio(self):
        # Calcula cantidad*precio_unitario - descuento línea
        qs = getattr(self, "lineas_servicio", None)
        if not qs:
            return Decimal("0")

        # Calcular subtotal con descuento en porcentaje
        expr = ExpressionWrapper(
            F("cantidad") * F("precio_unitario") * (1 - F("descuento") / 100),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
        total = qs.aggregate(s=Sum(expr)).get("s") or Decimal("0")
        return Decimal(total)

    def parts_subtotal(self):
        """Subtotal de líneas de repuesto (fuente de verdad para totales)."""
        return self._sum_repuesto()

    def services_subtotal(self):
        """Subtotal de líneas de servicio."""
        return self._sum_servicio()

    def doc_tax_amount(self):
        """
        Monto de impuesto según país: USA usa sales_tax_rate sobre (parts+services);
        otros países usan tasa sobre repuestos (recompute_totals).
        """
        from taller.models.configuracion import ConfiguracionEmpresa

        parts = self.parts_subtotal()
        services = self.services_subtotal()
        pais = getattr(self.empresa, "pais", "CL").upper()
        if pais == "US":
            config = getattr(self.empresa, "config", None)
            if not config:
                try:
                    config = ConfiguracionEmpresa.objects.filter(empresa=self.empresa).first()
                except Exception:
                    config = None
            rate = Decimal("0")
            if config and getattr(config, "sales_tax_rate", None) is not None:
                rate = Decimal(str(config.sales_tax_rate)) / Decimal("100")
            base = parts + services
            return (base * rate).quantize(Decimal("0.01"))
        return getattr(self, "tax_amount", Decimal("0")) or Decimal("0")

    def grand_total(self):
        """Parts + services + tax (y otros si aplica)."""
        parts = self.parts_subtotal()
        services = self.services_subtotal()
        otros = self._sum_otro_servicio()
        tax = self.doc_tax_amount()
        return self._q(parts + services + otros + tax)

    def _sum_otro_servicio(self):
        # Calcula cantidad * precio_cliente
        qs = getattr(self, "lineas_otro_servicio", None)
        if not qs:
            return Decimal("0")

        # precio_cliente puede ser null → coalesce 0
        expr = ExpressionWrapper(
            F("cantidad") * F("precio_cliente"),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
        total = qs.aggregate(s=Sum(expr)).get("s") or Decimal("0")
        return Decimal(total)

    def recompute_totals(self, persist=False):
        """
        Recalcula netos, impuesto y total conforme reglas:
        - El tax/IVA se aplica SOLO sobre repuestos en todos los países
        - Si apply_vat=True: aplica el tax_rate_applied sobre repuestos
        - Si apply_vat=False: no aplica impuesto
        - Si factura tiene servicios + repuestos → context = "mixed"
        """
        # Regla: factura con servicios y repuestos → context mixed; solo FAC, no PRES
        if self.pk and self.tipo == "FAC":
            has_serv = self.lineas_servicio.exists() if hasattr(self, "lineas_servicio") else False
            has_rep = self.lineas_repuesto.exists() if hasattr(self, "lineas_repuesto") else False

            if has_serv and has_rep:
                self.context = "mixed"
            else:
                # Si antes era mixed y ahora ya no mezcla, degradar contexto
                if getattr(self, "context", None) == "mixed":
                    if has_rep and not has_serv:
                        self.context = "parts"
                    elif has_serv and not has_rep:
                        self.context = "workshop"

        rep = self._sum_repuesto()
        srv = self._sum_servicio()
        osrv = self._sum_otro_servicio()

        rep = self._q(rep)
        srv = self._q(srv)
        osrv = self._q(osrv)

        # Descuento a nivel documento (si existe). Se asume aplicado al total final.
        desc = getattr(self, "descuento", Decimal("0")) or Decimal("0")
        desc = self._q(desc)

        # Tasa y base imponible por país
        from taller.models.configuracion import ConfiguracionEmpresa

        pais = getattr(self.empresa, "pais", "CL").upper()

        if pais == "US":
            # USA: sales_tax sobre (repuestos + servicios) si apply_vat
            config = (
                getattr(self.empresa, "config", None)
                or ConfiguracionEmpresa.objects.filter(empresa=self.empresa).first()
            )
            rate_pct = Decimal("0")
            if config and getattr(config, "sales_tax_rate", None) is not None:
                rate_pct = Decimal(str(config.sales_tax_rate))
            rate = rate_pct / Decimal("100")
            tax_base = (rep + srv) if getattr(self, "apply_vat", True) else Decimal("0")
            tax_amount = (tax_base * rate).quantize(Decimal("0.01"))
            rate = rate_pct  # para asignar tax_rate_applied en %
        else:
            rate = self._resolve_tax_rate()
            if getattr(self, "apply_vat", True):
                tax_base = rep
            else:
                tax_base = Decimal("0")
            tax_amount = tax_base * rate / Decimal("100.0")
            tax_amount = self._q(tax_amount)

        subtotal_general = rep + srv + osrv
        total = subtotal_general - desc + tax_amount
        total = self._q(total)

        # Asigna en instancia (no guardes aún salvo que persist=True)
        self.neto_repuestos = rep
        self.neto_servicios = srv
        self.neto_otros_servicios = osrv
        self.tax_rate_applied = rate
        self.tax_amount = tax_amount
        self.total = total

        if persist:
            update_fields = [
                "neto_repuestos",
                "neto_servicios",
                "neto_otros_servicios",
                "tax_rate_applied",
                "tax_amount",
                "total",
            ]
            if hasattr(self, "context"):
                update_fields.append("context")
            self.save(update_fields=update_fields)

    def clean(self):
        super().clean()
        empresa_id = getattr(self, "empresa_id", None)

        # Regla: OT siempre es workshop
        if self.tipo == "OT":
            self.context = "workshop"

        # Regla 3.4: técnico/vendedor pertenece a la empresa y está activo
        tecnico = getattr(self, "tecnico_responsable", None)
        if tecnico and empresa_id and tecnico.empresa_id != empresa_id:
            raise ValidationError(
                "El técnico responsable debe pertenecer a la misma empresa del documento."
            )
        if tecnico and not getattr(tecnico, "activo", True):
            raise ValidationError("El responsable asignado debe estar activo.")

        # Millas solo en USA
        if self.millas is not None and self.country != "US":
            raise ValidationError("El campo millas solo puede usarse en documentos de USA")

        # ✔ Consistencias críticas Cliente/Vehículo/Empresa
        if self.vehiculo_id:
            if not self.cliente_id:
                raise ValidationError("Debe seleccionar un cliente antes de asignar un vehículo.")

            # El vehículo debe pertenecer a la misma empresa del documento
            if (
                hasattr(self.vehiculo, "empresa_id")
                and empresa_id
                and self.vehiculo.empresa_id != empresa_id
            ):
                raise ValidationError(
                    "El vehículo seleccionado no pertenece a la empresa del documento."
                )

            # El vehículo debe pertenecer al cliente del documento
            if hasattr(self.vehiculo, "cliente_id") and self.vehiculo.cliente_id != self.cliente_id:
                raise ValidationError(
                    "El vehículo seleccionado no pertenece al cliente del documento."
                )

        # Validar que cliente pertenece a la empresa del documento
        if (
            self.cliente_id
            and empresa_id
            and hasattr(self.cliente, "empresa_id")
            and self.cliente.empresa_id != empresa_id
        ):
            raise ValidationError(
                "El cliente seleccionado no pertenece a la empresa del documento."
            )

        # Recalcular en validación (para vistas admin/FBV/CBV)
        # Nota: en creación con formsets, las líneas aún no existen → quedará 0
        # Por eso también recalculamos en save() y/o señales de líneas.
        # Solo recalcular si el documento ya tiene ID (no en creación)
        if self.pk:
            self.recompute_totals(persist=False)

    @property
    def numero_documento(self):
        """Retorna el número de documento con prefijo según tipo y país"""
        if not self.numero:
            return None

        # Si el número ya tiene prefijo (como "F001", "OT002"), devolverlo tal cual
        if self.numero.startswith(("F", "OT", "P", "E", "WO", "I")):
            return self.numero

        # Prefijos para Chile (CL)
        prefijos_cl = {
            "PRES": "E",  # Estimado
            "OT": "OT",  # Orden de Trabajo
            "FAC": "F",  # Factura
            "BOL": "B",  # Boleta
        }

        # Prefijos para USA
        prefijos_us = {
            "PRES": "E",  # Estimate
            "OT": "WO",  # Work Order
            "FAC": "I",  # Invoice
            "BOL": "I",  # Invoice (no hay boletas en USA)
        }

        prefijos = prefijos_us if self.country == "US" else prefijos_cl
        prefijo = prefijos.get(self.tipo, self.tipo)

        # Si el número es un string numérico, formatearlo
        try:
            numero_int = int(self.numero)
            return f"{prefijo}{numero_int:03d}"
        except (ValueError, TypeError):
            # Si no es numérico, devolver el número tal cual con prefijo
            return f"{prefijo}{self.numero}"

    @classmethod
    def get_next_number(cls, empresa, tipo="OT", context="workshop"):
        """
        Devuelve el próximo número de documento (preview, no consume secuencia).
        Para asignar al form initial en GET. Al guardar, generar_numero_documento() usará DocumentSequence.
        """
        tipo = (tipo or "OT").upper()
        qs = (
            cls.objects.filter(empresa=empresa, tipo=tipo)
            .exclude(numero__isnull=True)
            .exclude(numero__exact="")
        )
        max_seq = 0
        for num in qs.values_list("numero", flat=True).iterator():
            if not num:
                continue
            try:
                # Formato "WO-001" o "OT001"
                if "-" in str(num):
                    part = str(num).split("-")[-1]
                else:
                    part = "".join(c for c in str(num) if c.isdigit())
                n = int(part) if part else 0
                if n > max_seq:
                    max_seq = n
            except (ValueError, TypeError):
                continue
        next_n = max_seq + 1
        pais = getattr(empresa, "pais", "CL").upper()
        if pais == "US":
            prefijos = {"OT": "WO", "PRES": "E", "FAC": "I"}
        else:
            prefijos = {"OT": "OT", "PRES": "E", "FAC": "F"}
        prefix = prefijos.get(tipo, tipo[:2])
        return f"{prefix}-{next_n:03d}"

    def generar_numero_documento(self):
        """Genera el próximo número secuencial usando DocumentSequence por serie (context)."""
        if self.numero:
            return self.numero

        from taller.models.sequence import DocumentSequence

        # Determinar serie por context
        ctx = getattr(self, "context", "workshop") or "workshop"
        serie_map = {"workshop": "WORKSHOP", "parts": "PARTS", "mixed": "MIXED"}
        serie = serie_map.get(ctx, "WORKSHOP")

        # Prefijos USA-friendly por serie
        PREFIXES = {
            "WORKSHOP": {"OT": "WO", "PRES": "WQ", "FAC": "WI"},
            "PARTS": {"PRES": "PQ", "FAC": "PI"},
            "MIXED": {"FAC": "MI"},
        }
        prefixes = PREFIXES.get(serie, PREFIXES["WORKSHOP"])
        prefix = prefixes.get(self.tipo, self.tipo[:2] if self.tipo else "XX")

        n = DocumentSequence.next(self.empresa, self.tipo)
        self.numero = f"{prefix}{n:05d}"
        return self.numero

    def save(self, *args, **kwargs):
        """Override save para generar número automáticamente y recalcular totales"""
        # Asegura moneda/país por empresa si los tienes en el modelo de Documento
        if not getattr(self, "moneda", None) and getattr(self, "empresa", None):
            # Asignar moneda según país usando configuración centralizada
            from taller.utils.country_config import get_config_from_empresa

            config = get_config_from_empresa(self.empresa)
            self.moneda = config["currency"]
        if not getattr(self, "country", None) and getattr(self, "empresa", None):
            self.country = self.empresa.pais

        # Inicializar campos de totales si no tienen valor
        if self.legacy_total_repuestos is None:
            self.legacy_total_repuestos = Decimal("0")
        if self.legacy_total_servicios is None:
            self.legacy_total_servicios = Decimal("0")
        if self.legacy_total_otros is None:
            self.legacy_total_otros = Decimal("0")
        if self.legacy_iva is None:
            self.legacy_iva = Decimal("0")
        if self.legacy_total_general is None:
            self.legacy_total_general = Decimal("0")
        if not hasattr(self, "payment_status") or not self.payment_status:
            self.payment_status = "pending"

        if not self.numero:
            self.generar_numero_documento()

        # Primer guardado para obtener PK si no la tiene
        is_create = self.pk is None
        super().save(*args, **kwargs)

        # Solo recalcular si no estamos ya en una actualización de campos específicos
        # y si no estamos en una operación de bulk
        if "update_fields" not in kwargs and not kwargs.get("bulk_create", False):
            # Tras guardar, ya existen líneas (si se guardaron antes),
            # así que recalculamos y persistimos.
            # Evita loop infinito: no llames self.save() completo; solo update_fields.
            self.refresh_from_db()  # para ver líneas actuales
            self.recompute_totals(persist=True)

    @property
    def tipo_documento(self):
        return self.tipo

    @property
    def incluir_iva(self):
        return self.tax_rate_applied > 0

    @transaction.atomic
    def recalcular_totales(self, save=True):
        """
        Recalcula sumas usando ORM:
        - Repuestos: Sum(subtotal_expr) con descuento en %
        - Servicios: Sum(subtotal_expr) con descuento en %
        - Otros:     Sum(cantidad * precio_cliente)
        - IVA:       solo sobre repuestos (CL 19%, US 0)
        """
        from taller.models.lineas_documento import (
            LineaOtroServicio,
            LineaRepuesto,
            LineaServicio,
        )

        pais = getattr(self.empresa, "pais", "CL")

        zero_decimal = Value(
            Decimal("0"),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )

        rep = self.lineas_repuesto.aggregate(
            total=Coalesce(Sum(LineaRepuesto.subtotal_expr()), zero_decimal)
        )["total"]
        srv = self.lineas_servicio.aggregate(
            total=Coalesce(Sum(LineaServicio.subtotal_expr()), zero_decimal)
        )["total"]
        otr = self.lineas_otro_servicio.aggregate(
            total=Coalesce(Sum(LineaOtroServicio.subtotal_expr()), zero_decimal)
        )["total"]

        rep = Decimal(rep or 0)
        srv = Decimal(srv or 0)
        otr = Decimal(otr or 0)

        # ✅ Usar función centralizada de cálculo de impuestos
        from taller.impuestos.engine import calcular_impuesto

        # Calcular impuesto solo sobre repuestos (según convención del proyecto)
        iva_val = calcular_impuesto(rep, self.empresa, applies_to="parts")

        total = rep + srv + otr + iva_val

        neto_rep_q = money_quantize(rep, pais)
        neto_srv_q = money_quantize(srv, pais)
        neto_otr_q = money_quantize(otr, pais)
        iva_q = money_quantize(iva_val, pais)
        total_q = money_quantize(total, pais)

        self.neto_repuestos = neto_rep_q
        self.neto_servicios = neto_srv_q
        self.neto_otros_servicios = neto_otr_q
        self.tax_amount = iva_q
        self.total = total_q

        # Mantener columnas legacy sincronizadas
        self.legacy_total_repuestos = neto_rep_q
        self.legacy_total_servicios = neto_srv_q
        self.legacy_total_otros = neto_otr_q
        self.legacy_iva = iva_q
        self.legacy_total_general = total_q

        if save:
            update_fields = [
                "neto_repuestos",
                "neto_servicios",
                "neto_otros_servicios",
                "tax_amount",
                "total",
                "legacy_total_repuestos",
                "legacy_total_servicios",
                "legacy_total_otros",
                "legacy_iva",
                "legacy_total_general",
            ]

            self.save(update_fields=update_fields)

        return {
            "repuestos": self.neto_repuestos,
            "servicios": self.neto_servicios,
            "otros": self.neto_otros_servicios,
            "iva": self.tax_amount,
            "total": self.total,
        }

    @classmethod
    def recalcular_totales_bulk(cls, documento_ids):
        """
        Recalcula totales para múltiples documentos de forma eficiente.
        Útil para operaciones en lote o tareas asíncronas.
        """
        documentos = cls.objects.filter(id__in=documento_ids).select_related("empresa")
        for doc in documentos:
            doc.recompute_totals(persist=True)
        return len(documentos)

    # Propiedades retrocompatibles para compatibilidad con código y plantillas antiguas
    @property
    def repuestos(self):
        return self.lineas_repuesto

    @property
    def servicios(self):
        return self.lineas_servicio

    @property
    def otros_servicios(self):
        return self.lineas_otro_servicio

    # Propiedades de compatibilidad con el frontend antiguo
    @property
    def total_repuestos(self):
        return self.legacy_total_repuestos or Decimal("0")

    @total_repuestos.setter
    def total_repuestos(self, value):
        val = Decimal(value or 0)
        self.legacy_total_repuestos = val
        self.neto_repuestos = val

    @property
    def total_servicios(self):
        return self.legacy_total_servicios or Decimal("0")

    @total_servicios.setter
    def total_servicios(self, value):
        val = Decimal(value or 0)
        self.legacy_total_servicios = val
        self.neto_servicios = val

    @property
    def total_otros(self):
        return self.legacy_total_otros or Decimal("0")

    @total_otros.setter
    def total_otros(self, value):
        val = Decimal(value or 0)
        self.legacy_total_otros = val
        self.neto_otros_servicios = val

    @property
    def iva(self):
        return self.legacy_iva or Decimal("0")

    @iva.setter
    def iva(self, value):
        val = Decimal(value or 0)
        self.legacy_iva = val
        self.tax_amount = val

    @property
    def total_general(self):
        return self.legacy_total_general or Decimal("0")

    @total_general.setter
    def total_general(self, value):
        val = Decimal(value or 0)
        self.legacy_total_general = val
        self.total = val

    class Meta:
        app_label = "taller"
        verbose_name = _("Documento")
        verbose_name_plural = _("Documentos")
        indexes = [
            # Índices optimizados para KPIs
            models.Index(fields=["empresa", "fecha_emision"]),  # KPI por empresa y fecha
            models.Index(fields=["fecha_emision"]),  # KPI global por fecha
            models.Index(
                fields=["tecnico_responsable", "fecha_emision"]
            ),  # KPI por técnico y fecha
            models.Index(fields=["estado", "fecha_emision"]),  # KPI por estado y fecha
            models.Index(fields=["tipo", "fecha_emision"]),  # KPI por tipo y fecha
            # Índices de rendimiento general
            models.Index(fields=["tecnico_responsable"]),
            models.Index(fields=["cliente", "fecha_emision"]),  # Búsquedas por cliente
        ]
