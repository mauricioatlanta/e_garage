from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _  # 👈 Para traducciones

from taller.models.clientes import Cliente
from taller.models.mixins import AuditMixin
from taller.models.vehiculos import Vehiculo


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
            ("REC", _("Recibo/Boleta")),
            # ("FAC", _("Factura (LEGACY)")),  # Legacy, no mostrar en forms
            # ("BOL", _("Boleta (LEGACY)")),   # Legacy, no mostrar en forms
        ],
        db_index=True,
    )
    numero = models.CharField(max_length=32, blank=True, default="", db_index=True)
    correlativo = models.PositiveIntegerField(
        default=0, help_text=_("Número correlativo interno")
    )
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

    def clean(self):
        super().clean()
        empresa_id = getattr(self, "empresa_id", None)
        tecnico = getattr(self, "tecnico_responsable", None)
        tecnico_empresa_id = getattr(tecnico, "empresa_id", None) if tecnico else None
        if (
            empresa_id is not None
            and tecnico_empresa_id is not None
            and empresa_id != tecnico_empresa_id
        ):
            raise ValidationError(
                "El técnico responsable debe pertenecer a la misma empresa del documento."
            )

        # Validar que millas solo se use en USA
        if self.millas is not None and self.country != "US":
            raise ValidationError(
                "El campo millas solo puede usarse en documentos de USA"
            )

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
        """Override save para generar número automáticamente"""
        if not self.numero:
            self.generar_numero_documento()
        super().save(*args, **kwargs)

    @property
    def tipo_documento(self):
        return self.tipo

    @property
    def incluir_iva(self):
        return self.tax_rate_applied > 0

    def total_repuestos(self):
        # Calcular usando campos reales de BD (cantidad * precio_unitario * (1 - descuento/100))
        from django.db.models import DecimalField, F, Sum, Value
        from django.db.models.functions import Coalesce

        return (
            self.lineas_repuesto.aggregate(
                total=Coalesce(
                    Sum(
                        F("cantidad")
                        * F("precio_unitario")
                        * (1 - F("descuento") / 100),
                        output_field=DecimalField(max_digits=12, decimal_places=2),
                    ),
                    Value(
                        0, output_field=DecimalField(max_digits=12, decimal_places=2)
                    ),
                )
            )["total"]
            or 0
        )

    def total_servicios(self):
        # Calcular usando campos reales de BD (cantidad * precio_unitario * (1 - descuento/100))
        from django.db.models import DecimalField, F, Sum, Value
        from django.db.models.functions import Coalesce

        return (
            self.lineas_servicio.aggregate(
                total=Coalesce(
                    Sum(
                        F("cantidad")
                        * F("precio_unitario")
                        * (1 - F("descuento") / 100),
                        output_field=DecimalField(max_digits=12, decimal_places=2),
                    ),
                    Value(
                        0, output_field=DecimalField(max_digits=12, decimal_places=2)
                    ),
                )
            )["total"]
            or 0
        )

    def total_otros_servicios(self):
        # LineaOtroServicio no siempre tiene 'subtotal'; calculamos precio_cliente * cantidad
        from django.db.models import DecimalField, F, Sum, Value
        from django.db.models.functions import Coalesce

        return (
            self.lineas_otro_servicio.aggregate(
                total=Coalesce(
                    Sum(
                        F("precio_cliente") * F("cantidad"),
                        output_field=DecimalField(max_digits=12, decimal_places=2),
                    ),
                    Value(
                        0, output_field=DecimalField(max_digits=12, decimal_places=2)
                    ),
                )
            )["total"]
            or 0
        )

    def iva(self):
        subtotal = (
            self.total_repuestos()
            + self.total_servicios()
            + self.total_otros_servicios()
            - float(self.descuento)
        )
        return subtotal * float(self.tax_rate_applied) / 100 if self.incluir_iva else 0

    def total_general(self):
        return (
            (self.total_repuestos() or 0)
            + (self.total_servicios() or 0)
            + (self.total_otros_servicios() or 0)
        )

    def recalcular_totales(self):
        """Recalcula y actualiza los totales del documento aplicando IVA solo a repuestos"""

        # Subtotales "autoridad" en servidor
        rep_sub = (
            self.lineas_repuesto.annotate(
                sub=ExpressionWrapper(
                    F("cantidad") * F("precio_unitario"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            ).aggregate(total=Sum("sub"))["total"]
            or 0
        )

        serv_sub = (
            self.lineas_servicio.annotate(
                sub=ExpressionWrapper(
                    F("cantidad") * F("precio_unitario"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            ).aggregate(total=Sum("sub"))["total"]
            or 0
        )

        otros_sub = (
            self.lineas_otro_servicio.annotate(
                sub=ExpressionWrapper(
                    F("cantidad") * F("precio_cliente"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            ).aggregate(total=Sum("sub"))["total"]
            or 0
        )

        self.neto_repuestos = rep_sub
        self.neto_servicios = serv_sub + otros_sub

        # IVA Chile solo sobre repuestos
        if self.country == "CL" and (self.apply_vat or self.apply_vat is None):
            self.tax_rate_applied = self.tax_rate_applied or 19
            self.tax_amount = rep_sub * (self.tax_rate_applied / 100)
        else:
            self.tax_amount = 0

        self.total = self.neto_repuestos + self.neto_servicios + self.tax_amount

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
