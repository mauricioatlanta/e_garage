from decimal import Decimal, ROUND_HALF_UP

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
    neto_repuestos = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    neto_servicios = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    neto_otros_servicios = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    descuento = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    tax_rate_applied = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    tax_amount = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    total = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00")
    )
    
    # Campos de totales con nombres estándar para compatibilidad con frontend
    total_repuestos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_servicios = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_otros = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_general = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    # Opcional: estado de pago
    payment_status = models.CharField(max_length=20, blank=True, default='pending')
    
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
    apply_vat = models.BooleanField(
        default=True, help_text=_("Aplicar IVA al documento")
    )
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
        help_text=_("Método de pago utilizado")
    )
    ult4 = models.CharField(
        max_length=4,
        blank=True,
        null=True,
        help_text=_("Últimos 4 dígitos de tarjeta (si aplica)")
    )
    monto_pagado = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00"),
        help_text=_("Monto efectivamente pagado")
    )
    saldo_pendiente = models.DecimalField(
        max_digits=14, decimal_places=2, default=Decimal("0.00"),
        help_text=_("Saldo pendiente de pago")
    )
    fecha_pago = models.DateTimeField(
        blank=True, null=True,
        help_text=_("Fecha y hora del pago")
    )
    nota_pago = models.TextField(
        blank=True, null=True,
        help_text=_("Notas adicionales sobre el pago")
    )

    # --------- Helpers internos ---------
    def vat_percent(self) -> int:
        """IVA por país (regla del proyecto)"""
        return 19 if getattr(self.empresa, "pais", "CL") == "CL" else 0

    def _decimals(self):
        """
        Decimales por país/moneda: US -> 2, CL -> 0 (según regla eGarage).
        """
        try:
            pais = (self.empresa.pais or "CL").upper()
        except Exception:
            pais = "CL"
        return 2 if pais == "US" else 0

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
            if config and hasattr(config, 'tasa_iva') and config.tasa_iva is not None:
                return Decimal(str(config.tasa_iva))
        except (ImportError, AttributeError, Exception):
            pass
        
        # Valores por defecto por país
        try:
            pais = (self.empresa.pais or "CL").upper()
        except Exception:
            pais = "CL"
        return Decimal("19.0") if pais == "CL" else Decimal("0.0")

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
        - CL: IVA 19% SOLO sobre repuestos
        - US: por defecto 0% (usa tax_rate_applied si viene)
        """
        rep = self._sum_repuesto()
        srv = self._sum_servicio()
        osrv = self._sum_otro_servicio()

        rep = self._q(rep)
        srv = self._q(srv)
        osrv = self._q(osrv)

        # Descuento a nivel documento (si existe). Se asume aplicado al total final.
        desc = getattr(self, "descuento", Decimal("0")) or Decimal("0")
        desc = self._q(desc)

        # Tasa
        rate = self._resolve_tax_rate()  # ej. 19.0 o 0.0
        # Base imponible por país
        try:
            pais = (self.empresa.pais or "CL").upper()
        except Exception:
            pais = "CL"

        if pais == "CL":
            tax_base = rep  # IVA solo a repuestos
        else:  # US - usar apply_vat para determinar base imponible
            # Si apply_vat=True, aplicar impuesto a repuestos + servicios
            # Si apply_vat=False, no aplicar impuesto
            if getattr(self, "apply_vat", True):
                tax_base = rep + srv  # Repuestos + servicios
            else:
                tax_base = Decimal("0")  # Sin impuesto

        tax_amount = (tax_base * rate / Decimal("100.0"))
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
            self.save(update_fields=[
                "neto_repuestos", "neto_servicios", "neto_otros_servicios",
                "tax_rate_applied", "tax_amount", "total"
            ])

    def clean(self):
        super().clean()
        empresa_id = getattr(self, "empresa_id", None)

        # Técnico pertenece a la empresa
        tecnico = getattr(self, "tecnico_responsable", None)
        if tecnico and empresa_id and tecnico.empresa_id != empresa_id:
            raise ValidationError("El técnico responsable debe pertenecer a la misma empresa del documento.")

        # Millas solo en USA
        if self.millas is not None and self.country != "US":
            raise ValidationError("El campo millas solo puede usarse en documentos de USA")

        # ✔ Consistencias críticas Cliente/Vehículo/Empresa
        if self.vehiculo_id:
            if not self.cliente_id:
                raise ValidationError("Debe seleccionar un cliente antes de asignar un vehículo.")

            # El vehículo debe pertenecer a la misma empresa del documento
            if hasattr(self.vehiculo, "empresa_id") and empresa_id and self.vehiculo.empresa_id != empresa_id:
                raise ValidationError("El vehículo seleccionado no pertenece a la empresa del documento.")

            # El vehículo debe pertenecer al cliente del documento
            if hasattr(self.vehiculo, "cliente_id") and self.vehiculo.cliente_id != self.cliente_id:
                raise ValidationError("El vehículo seleccionado no pertenece al cliente del documento.")

        # Validar que cliente pertenece a la empresa del documento
        if self.cliente_id and empresa_id and hasattr(self.cliente, "empresa_id") and self.cliente.empresa_id != empresa_id:
            raise ValidationError("El cliente seleccionado no pertenece a la empresa del documento.")

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

    def generar_numero_documento(self):
        """Genera el próximo número secuencial para el tipo de documento"""
        if self.numero:
            return self.numero

        # Buscar el último número para este tipo de documento en esta empresa
        ultimo_doc = (
            Documento.objects.filter(empresa=self.empresa, tipo=self.tipo)
            .order_by("-numero")
            .first()
        )

        if ultimo_doc and ultimo_doc.numero:
            # Convertir el número a entero, sumar 1, y volver a string
            try:
                numero_anterior = int(ultimo_doc.numero)
                self.numero = str(numero_anterior + 1)
            except (ValueError, TypeError):
                # Si no se puede convertir a entero, empezar desde 1
                self.numero = "1"
        else:
            self.numero = "1"

        return self.numero

    def save(self, *args, **kwargs):
        """Override save para generar número automáticamente y recalcular totales"""
        # Asegura moneda/país por empresa si los tienes en el modelo de Documento
        if not getattr(self, "moneda", None) and getattr(self, "empresa", None):
            self.moneda = "USD" if self.empresa.pais == "US" else "CLP"
        if not getattr(self, "country", None) and getattr(self, "empresa", None):
            self.country = self.empresa.pais

        # Inicializar campos de totales si no tienen valor
        if not hasattr(self, 'total_repuestos') or self.total_repuestos is None:
            self.total_repuestos = Decimal("0")
        if not hasattr(self, 'total_servicios') or self.total_servicios is None:
            self.total_servicios = Decimal("0")
        if not hasattr(self, 'total_otros') or self.total_otros is None:
            self.total_otros = Decimal("0")
        if not hasattr(self, 'iva') or self.iva is None:
            self.iva = Decimal("0")
        if not hasattr(self, 'total_general') or self.total_general is None:
            self.total_general = Decimal("0")
        if not hasattr(self, 'payment_status') or not self.payment_status:
            self.payment_status = "pending"

        if not self.numero:
            self.generar_numero_documento()

        # Primer guardado para obtener PK si no la tiene
        is_create = self.pk is None
        super().save(*args, **kwargs)

        # Solo recalcular si no estamos ya en una actualización de campos específicos
        # y si no estamos en una operación de bulk
        if 'update_fields' not in kwargs and not kwargs.get('bulk_create', False):
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

    # Métodos de compatibilidad (usando los nuevos campos calculados)
    def total_repuestos(self):
        """Compatibilidad: retorna neto_repuestos"""
        return self.neto_repuestos or Decimal("0")

    def total_servicios(self):
        """Compatibilidad: retorna neto_servicios"""
        return self.neto_servicios or Decimal("0")

    def total_otros_servicios(self):
        """Compatibilidad: retorna neto_otros_servicios"""
        return self.neto_otros_servicios or Decimal("0")

    def iva(self):
        """Compatibilidad: retorna tax_amount"""
        return self.tax_amount or Decimal("0")

    def total_general(self):
        """Compatibilidad: retorna total"""
        return self.total or Decimal("0")

    @transaction.atomic
    def recalcular_totales(self, save=True):
        """
        Recalcula sumas usando ORM:
        - Repuestos: Sum(cantidad*precio_unitario - descuento)
        - Servicios: Sum(cantidad*precio_unitario - descuento)
        - Otros:     Sum(precio_cliente * cantidad)
        - IVA:       solo sobre repuestos (CL 19%, US 0)
        """
        pais = getattr(self.empresa, "pais", "CL")

        # Expresiones por tipo
        rep_expr = ExpressionWrapper(
            (F("cantidad") * F("precio_unitario")) - Coalesce(F("descuento"), Value(0)),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
        serv_expr = ExpressionWrapper(
            (F("cantidad") * F("precio_unitario")) - Coalesce(F("descuento"), Value(0)),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
        otros_expr = ExpressionWrapper(
            (F("cantidad") * F("precio_cliente")),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )

        rep = self.lineas_repuesto.aggregate(total=Coalesce(Sum(rep_expr), Value(0)))["total"]
        srv = self.lineas_servicio.aggregate(total=Coalesce(Sum(serv_expr), Value(0)))["total"]
        otr = self.lineas_otro_servicio.aggregate(total=Coalesce(Sum(otros_expr), Value(0)))["total"]

        rep = Decimal(rep or 0)
        srv = Decimal(srv or 0)
        otr = Decimal(otr or 0)

        iva_pct = self.vat_percent()
        iva_val = (rep * Decimal(iva_pct)) / Decimal(100)

        total = rep + srv + otr + iva_val

        # Redondeo por país
        self.total_repuestos = money_quantize(rep, pais)
        self.total_servicios = money_quantize(srv, pais)
        self.total_otros = money_quantize(otr, pais)
        self.iva = money_quantize(iva_val, pais)
        self.total_general = money_quantize(total, pais)

        if save:
            self.save(update_fields=["total_repuestos", "total_servicios", "total_otros", "iva", "total_general"])

        return {
            "repuestos": self.total_repuestos,
            "servicios": self.total_servicios,
            "otros": self.total_otros,
            "iva": self.iva,
            "total": self.total_general,
        }
    
    @classmethod
    def recalcular_totales_bulk(cls, documento_ids):
        """
        Recalcula totales para múltiples documentos de forma eficiente.
        Útil para operaciones en lote o tareas asíncronas.
        """
        documentos = cls.objects.filter(id__in=documento_ids).select_related('empresa')
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

    class Meta:
        app_label = "taller"
        verbose_name = _("Documento")
        verbose_name_plural = _("Documentos")
        indexes = [
            # Índices optimizados para KPIs
            models.Index(
                fields=["empresa", "fecha_emision"]
            ),  # KPI por empresa y fecha
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
