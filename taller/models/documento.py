import uuid
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
    tipo = models.CharField(
        max_length=4,
        choices=[
            ("OT", _("Orden de Trabajo")),
            ("PRES", _("Presupuesto")),
            ("FAC", _("Comprobante")),
            ("PTS", _("Venta Repuestos")),
            # ("REC", _("Recibo (LEGACY)")),  # Legacy, no mostrar en forms
            # ("BOL", _("Boleta (LEGACY)")),   # Legacy, no mostrar en forms
        ],
        db_index=True,
    )
    numero = models.CharField(max_length=32, blank=True, default="", db_index=True)
    # uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
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
    # Camino nuevo en paralelo a 'vehiculo' (mismo patrón que 0142/0152): FK
    # nullable a VehiculoDesarme, sin tocar 'vehiculo'. Se usa cuando el
    # origen es una venta de desarme (tipo=PTS) sobre un VehiculoDesarme
    # directo, sin Vehiculo real detrás -- ver
    # taller/desarme/views_inventario.py:finalizar_venta_desde_inventario.
    vehiculo_desarme = models.ForeignKey(
        "taller.VehiculoDesarme",
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

    # Opcional: estado de pago
    payment_status = models.CharField(max_length=20, blank=True, default="pending")

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
    approved_at = models.DateTimeField(
        blank=True,
        null=True,
        db_index=True,
        help_text=_("Fecha y hora en que el cliente aprobo el presupuesto"),
    )
    approved_by = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text=_("Nombre del cliente que aprobo el presupuesto"),
    )
    approved_ip = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text=_("Direccion IP desde la cual se aprobo el presupuesto"),
    )

    # --------- Helpers internos ---------
    def get_public_url(self, request=None):
        """
        Retorna la URL publica del presupuesto para revision/aprobacion.
        """
        if self.tipo != "PRES" or not self.uuid:
            return None

        from django.conf import settings
        from django.urls import reverse

        path = reverse("publico:ver_presupuesto", kwargs={"uuid": self.uuid})
        if request is not None:
            return request.build_absolute_uri(path)

        base_url = (
            getattr(settings, "SITE_URL", None)
            or getattr(settings, "BASE_URL", None)
            or "https://egarage.cl"
        ).rstrip("/")
        return f"{base_url}{path}"

    @property
    def is_approved(self):
        return self.approved_at is not None

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
                current_rate = Decimal(str(self.tax_rate_applied))
                if current_rate != Decimal("0"):
                    return current_rate
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
        if qs is None:
            return Decimal("0")
        total = Decimal("0")
        for linea in qs.all():
            total += Decimal(getattr(linea, "subtotal", Decimal("0")) or Decimal("0"))
        return total

    def _sum_servicio(self):
        # Calcula cantidad*precio_unitario - descuento línea
        qs = getattr(self, "lineas_servicio", None)
        if qs is None:
            return Decimal("0")
        total = Decimal("0")
        for linea in qs.all():
            total += Decimal(getattr(linea, "subtotal", Decimal("0")) or Decimal("0"))
        return total

    def _sum_otro_servicio(self):
        # Calcula cantidad * precio_cliente
        qs = getattr(self, "lineas_otro_servicio", None)
        if qs is None:
            return Decimal("0")

        # precio_cliente puede ser null → coalesce 0
        total = Decimal("0")
        for linea in qs.all():
            total += Decimal(getattr(linea, "subtotal", Decimal("0")) or Decimal("0"))
        return total

    def recompute_totals(self, persist=False):
        """
        Recalcula netos, impuesto y total conforme reglas:
        - El tax/IVA se aplica SOLO sobre repuestos en todos los países
        - Si apply_vat=True: aplica el tax_rate_applied sobre repuestos
        - Si apply_vat=False: no aplica impuesto
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
        # Base imponible por país usando configuración centralizada
        from taller.utils.country_config import get_config_from_documento

        config = get_config_from_documento(self)
        pais = getattr(self.empresa, "pais", "CL").upper()

        # Regla: Tax/IVA SOLO sobre repuestos en todos los países
        # Si apply_vat=True, aplicar impuesto solo a repuestos
        # Si apply_vat=False, no aplicar impuesto
        if getattr(self, "apply_vat", True):
            tax_base = rep  # Tax solo a repuestos (no servicios)
        else:
            tax_base = Decimal("0")  # Sin impuesto

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
            self.save(
                update_fields=[
                    "neto_repuestos",
                    "neto_servicios",
                    "neto_otros_servicios",
                    "tax_rate_applied",
                    "tax_amount",
                    "total",
                ]
            )

    def clean(self):
        super().clean()
        empresa_id = getattr(self, "empresa_id", None)

        # Técnico pertenece a la empresa
        tecnico = getattr(self, "tecnico_responsable", None)
        if tecnico and empresa_id and tecnico.empresa_id != empresa_id:
            raise ValidationError(
                "El técnico responsable debe pertenecer a la misma empresa del documento."
            )

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

            # El vehículo debe pertenecer al cliente del documento (solo si tiene cliente; desarme no aplica aquí)
            if (
                getattr(self.vehiculo, "cliente_id", None) is not None
                and self.vehiculo.cliente_id != self.cliente_id
            ):
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

        # Recibo/Invoice (correlativo PRO): REC-000001, INV-000001
        if self.numero.startswith(("REC-", "INV-")):
            return self.numero

        # Si el número ya tiene prefijo (como "F001", "OT002"), devolverlo tal cual
        if self.numero.startswith(("F", "OT", "P", "E", "WO", "I")):
            return self.numero

        # Prefijos para Chile (CL)
        prefijos_cl = {
            "PRES": "E",  # Estimado
            "OT": "OT",  # Orden de Trabajo
            "FAC": "F",  # Factura
            "PTS": "PS",  # Part Sale / Venta de repuestos
            "BOL": "B",  # Boleta
        }

        # Prefijos para USA
        prefijos_us = {
            "PRES": "E",  # Estimate
            "OT": "WO",  # Work Order
            "FAC": "I",  # Invoice
            "PTS": "PS",  # Part Sale
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

    @transaction.atomic
    def generar_numero_documento(self):
        """
        Genera correlativo seguro evitando race conditions.
        Usa DocumentSequence con select_for_update para garantizar unicidad.
        Al primer uso siembra el contador desde los documentos existentes.
        """
        import re
        from taller.models.sequence import DocumentSequence

        if self.numero:
            return self.numero

        seq, _ = DocumentSequence.objects.select_for_update().get_or_create(
            empresa=self.empresa,
            tipo=self.tipo,
            defaults={"current": 0},
        )

        if seq.current == 0:
            # Siembra el contador con el máximo existente para esta empresa/tipo
            for valor in (
                Documento.objects
                .filter(empresa=self.empresa, tipo=self.tipo)
                .exclude(numero__isnull=True)
                .exclude(numero="")
                .values_list("numero", flat=True)
            ):
                m = re.search(r"(\d+)$", str(valor).strip())
                if m:
                    try:
                        seq.current = max(seq.current, int(m.group(1)))
                    except Exception:
                        pass

        seq.current += 1
        seq.save(update_fields=["current"])
        self.numero = str(seq.current)

        return self.numero

    def convertir_documento_final(self):
        """
        Conversión operacional automática:

        Chile:
            PRES -> OT

        USA:
            PRES -> FAC

        Mantiene el mismo documento,
        pero cambia:
        - tipo
        - correlativo
        - prefijo
        """

        if self.tipo != "PRES":
            return False

        nuevo_tipo = "FAC" if self.country == "US" else "OT"

        self.tipo = nuevo_tipo

        # Forzar regeneración de número
        self.numero = ""

        self.generar_numero_documento()

        self.save(update_fields=["tipo", "numero"])

        return True



    def save(self, *args, **kwargs):
        """Override save para generar número automáticamente y recalcular totales"""
        # Asegura moneda/país por empresa si los tienes en el modelo de Documento
        if not getattr(self, "moneda", None) and getattr(self, "empresa", None):
            # Asignar moneda según país usando configuración centralizada
            from taller.utils.country_config import get_config_from_empresa

            config = get_config_from_empresa(self.empresa)
            self.moneda = config["currency"]
        if getattr(self, "empresa", None) and getattr(self.empresa, "pais", None):
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

        if self.pk is None:
            # Siempre regenerar para nuevos registros: evita race conditions
            # cuando el form pre-rellena 'numero' desde una llamada AJAX previa.
            self.numero = ""
            self.generar_numero_documento()
        elif not self.numero:
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
        - Repuestos: Sum(cantidad*precio_unitario - descuento)
        - Servicios: Sum(cantidad*precio_unitario - descuento)
        - Otros:     Sum(precio_cliente * cantidad)
        - IVA:       solo sobre repuestos (CL 19%, US 0)
        """
        pais = getattr(self.empresa, "pais", "CL")

        # Expresiones por tipo
        rep_expr = ExpressionWrapper(
            F("cantidad")
            * F("precio_unitario")
            * (
                Value(Decimal("1.00"))
                - (Coalesce(F("descuento"), Value(Decimal("0.00"))) / Value(Decimal("100.00")))
            ),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
        serv_expr = ExpressionWrapper(
            F("cantidad")
            * F("precio_unitario")
            * (
                Value(Decimal("1.00"))
                - (Coalesce(F("descuento"), Value(Decimal("0.00"))) / Value(Decimal("100.00")))
            ),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )
        otros_expr = ExpressionWrapper(
            (F("cantidad") * F("precio_cliente")),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )

        zero_decimal = Value(
            Decimal("0"),
            output_field=DecimalField(max_digits=14, decimal_places=2),
        )

        rep = self.lineas_repuesto.aggregate(total=Coalesce(Sum(rep_expr), zero_decimal))["total"]
        srv = self.lineas_servicio.aggregate(total=Coalesce(Sum(serv_expr), zero_decimal))["total"]
        otr = self.lineas_otro_servicio.aggregate(total=Coalesce(Sum(otros_expr), zero_decimal))[
            "total"
        ]

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
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "tipo", "numero"],
                name="uniq_documento_empresa_tipo_numero",
            )
        ]
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
