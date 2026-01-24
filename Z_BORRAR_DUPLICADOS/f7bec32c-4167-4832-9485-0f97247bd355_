# -*- coding: utf-8 -*-
"""
Catálogo de Repuestos con I18N y precios multi-empresa

Convenciones del proyecto:
- FKs como string ('app.Model') para lazy references
- Internacionalización con tablas separadas (*I18N)
- Precios por empresa con validez temporal
- TaxPolicy reutilizable para repuestos y servicios
"""
from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _


class TaxPolicy(models.Model):
    """
    Política de impuestos para aplicar a repuestos/servicios por ubicación.

    Reglas por país (convenciones del proyecto):
    - Chile: IVA 19% solo a repuestos (no servicios)
    - USA: sales tax por estado/ciudad
    - Brasil: ICMS por estado (~18%)
    - Venezuela: IVA 16%
    - Perú: IGV 18%
    """

    country = models.CharField(
        _("País"),
        max_length=2,
        choices=[
            ("CL", "Chile"),
            ("US", "USA"),
            ("MX", "México"),
            ("BR", "Brasil"),
            ("PE", "Perú"),
            ("VE", "Venezuela"),
        ],
        help_text="País donde aplica esta política",
    )
    state_code = models.CharField(
        _("Código de Estado"),
        max_length=10,
        blank=True,
        default="",
        help_text="Código de estado (opcional, para granularidad por estado)",
    )
    city_name = models.CharField(
        _("Ciudad"),
        max_length=80,
        blank=True,
        default="",
        help_text="Ciudad específica (opcional, para granularidad por ciudad)",
    )
    applies_to = models.CharField(
        _("Aplica a"),
        max_length=10,
        choices=(
            ("parts", "Repuestos"),
            ("services", "Servicios"),
            ("both", "Ambos"),
        ),
        default="parts",
        help_text="A qué tipo de items aplica este impuesto",
    )
    rate = models.DecimalField(
        _("Tasa"),
        max_digits=5,
        decimal_places=4,
        help_text="Tasa de impuesto (0.1900 para 19%, 0.1800 para 18%)",
    )
    inclusive = models.BooleanField(
        _("Incluido en precio"),
        default=False,
        help_text="¿El impuesto está incluido en el precio de venta?",
    )
    active = models.BooleanField(
        _("Activo"), default=True, help_text="Si esta política está activa"
    )

    # Metadata
    created_at = models.DateTimeField(_("Fecha de Creación"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Fecha de Actualización"), auto_now=True)

    class Meta:
        verbose_name = _("Política de Impuestos")
        verbose_name_plural = _("Políticas de Impuestos")
        ordering = ["country", "state_code", "city_name"]
        indexes = [
            # ✅ Índice compuesto principal para búsqueda de políticas
            models.Index(
                fields=["country", "state_code", "city_name", "applies_to", "active"],
                name="idx_taxpolicy_lookup",
            ),
            # Índices auxiliares
            models.Index(fields=["country", "active"], name="idx_taxpolicy_country"),
            models.Index(fields=["country", "state_code"], name="idx_taxpolicy_state"),
        ]

    def __str__(self):
        scope = self.country
        if self.state_code:
            scope += f"-{self.state_code}"
        if self.city_name:
            scope += f"-{self.city_name}"
        return f"{scope} {self.applies_to} {float(self.rate * 100):.2f}%"

    @property
    def rate_percentage(self):
        """Tasa como porcentaje (ej: 19.0 para 0.19)"""
        return float(self.rate * 100)


class Part(models.Model):
    """
    Repuesto en el catálogo (multi-empresa).

    Cada empresa puede tener sus propios repuestos, o usar catálogo compartido.
    Los nombres se manejan vía PartI18N para internacionalización.
    """

    # Multi-tenant: empresa opcional (null = catálogo global)
    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="parts",
        null=True,
        blank=True,
        help_text="Empresa propietaria (null = catálogo global compartido)",
    )

    # Identificación
    sku = models.CharField(
        _("SKU"),
        max_length=64,
        unique=True,
        db_index=True,  # ✅ Índice para búsquedas rápidas por SKU
        help_text="Código único del repuesto (SKU/Part Number)",
    )
    category = models.CharField(
        _("Categoría"),
        max_length=64,
        help_text="Categoría del repuesto (ej: filtros, frenos, aceites)",
    )
    brand = models.CharField(
        _("Marca"),
        max_length=64,
        blank=True,
        default="",
        help_text="Marca del repuesto (ej: Bosch, NGK, Mobil)",
    )

    # Unidad de medida y peso
    unit = models.CharField(
        _("Unidad"), max_length=16, default="un", help_text="Unidad de venta (un, lt, kg, m, set)"
    )
    weight_kg = models.DecimalField(
        _("Peso (kg)"),
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Peso en kilogramos (para shipping)",
    )

    # Precio de compra/costo
    purchase_price = models.DecimalField(
        _("Precio de Compra"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Costo de adquisición del repuesto",
    )

    # Stock (opcional - para futuras funcionalidades)
    stock_quantity = models.DecimalField(
        _("Stock"),
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Cantidad en stock",
    )
    stock_min = models.DecimalField(
        _("Stock Mínimo"),
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Stock mínimo para alerta",
    )

    # Status
    active = models.BooleanField(
        _("Activo"), default=True, help_text="Si el repuesto está disponible para venta"
    )

    # Metadata
    created_at = models.DateTimeField(_("Fecha de Creación"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Fecha de Actualización"), auto_now=True)

    class Meta:
        verbose_name = _("Repuesto")
        verbose_name_plural = _("Repuestos")
        ordering = ["sku"]
        indexes = [
            models.Index(fields=["empresa", "sku"]),
            models.Index(fields=["empresa", "category"]),
            models.Index(fields=["empresa", "brand"]),
            models.Index(fields=["active"]),
        ]

    def __str__(self):
        return self.sku

    def get_display_name(self, locale="es-CL"):
        """
        Obtener nombre localizado del repuesto con fallback inteligente.

        Estrategia de fallback:
        1. Buscar locale exacto (ej: es-PE)
        2. Fallback a es-CL (idioma por defecto del sistema)
        3. Fallback al primer I18N disponible
        4. Fallback al SKU si no hay I18N

        Args:
            locale (str): Código de locale (ej: 'es-CL', 'en-US', 'pt-BR')

        Returns:
            str: Nombre localizado o SKU como fallback

        Ejemplos:
            >>> part.get_display_name('es-CL')  # Exacto
            'Aceite de Motor 5W30'
            >>> part.get_display_name('es-PE')  # Fallback a es-CL
            'Aceite de Motor 5W30'
            >>> part.get_display_name('fr-FR')  # Fallback a primer disponible
            'Aceite de Motor 5W30'
        """
        # 1. Intentar locale exacto
        try:
            i18n = self.i18n.get(locale=locale)
            return i18n.display_name
        except PartI18N.DoesNotExist:
            pass

        # 2. Fallback a es-CL (idioma por defecto)
        if locale != "es-CL":
            try:
                i18n = self.i18n.get(locale="es-CL")
                return i18n.display_name
            except PartI18N.DoesNotExist:
                pass

        # 3. Fallback al primer I18N disponible
        i18n = self.i18n.first()
        if i18n:
            return i18n.display_name

        # 4. Fallback al SKU
        return self.sku

    def get_price(self, empresa, fecha=None):
        """
        Obtener precio vigente para una empresa en una fecha específica.

        Estrategia de búsqueda:
        1. Buscar precio de la empresa específica vigente en la fecha
        2. Fallback a precio global (company=NULL) si está permitido

        Args:
            empresa (Empresa): Empresa para la cual obtener el precio
            fecha (date, optional): Fecha de vigencia. Por defecto: hoy

        Returns:
            PartPrice or None: Registro de precio vigente, o None si no existe

        Ejemplos:
            >>> price = part.get_price(empresa)
            >>> if price:
            ...     print(f"{price.currency} {price.price}")
            'CLP 25000'

            >>> price = part.get_price(empresa, date(2025, 6, 15))
            >>> print(price.price if price else 'Sin precio')
        """
        from datetime import date

        if fecha is None:
            fecha = date.today()

        # 1. Buscar precio de la empresa específica
        price = (
            self.prices.filter(company=empresa, valid_from__lte=fecha)
            .filter(models.Q(valid_to__gte=fecha) | models.Q(valid_to__isnull=True))
            .order_by("-valid_from")
            .first()
        )

        if price:
            return price

        # 2. Fallback a precio global (company=NULL) si existe
        price_global = (
            self.prices.filter(company__isnull=True, valid_from__lte=fecha)
            .filter(models.Q(valid_to__gte=fecha) | models.Q(valid_to__isnull=True))
            .order_by("-valid_from")
            .first()
        )

        return price_global


class PartI18N(models.Model):
    """
    Nombres localizados para repuestos (I18N).

    Permite tener nombres diferentes por país/idioma:
    - es-CL: "Aceite de Motor 5W30"
    - en-US: "Engine Oil 5W30"
    - pt-BR: "Óleo de Motor 5W30"
    - es-PE: "Aceite para Motor 5W30"
    - es-VE: "Aceite de Motor 5W30"
    """

    part = models.ForeignKey(
        "taller.Part",  # ✅ String reference (mismo app actualmente, preparar para repuestos.Part en futuro)
        on_delete=models.CASCADE,
        related_name="i18n",
        verbose_name=_("Repuesto"),
    )
    locale = models.CharField(
        _("Locale"),
        max_length=8,
        help_text="Código de idioma-país (ej: es-CL, en-US, pt-BR, es-PE, es-VE)",
    )
    display_name = models.CharField(
        _("Nombre para Mostrar"), max_length=160, help_text="Nombre del repuesto en este idioma"
    )
    synonyms = models.TextField(
        _("Sinónimos"),
        blank=True,
        default="",
        help_text="Sinónimos separados por coma (para búsqueda)",
    )

    # Metadata
    created_at = models.DateTimeField(_("Fecha de Creación"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Fecha de Actualización"), auto_now=True)

    class Meta:
        verbose_name = _("Nombre de Repuesto (I18N)")
        verbose_name_plural = _("Nombres de Repuestos (I18N)")
        unique_together = ("part", "locale")
        indexes = [
            models.Index(fields=["part", "locale"]),
            models.Index(fields=["locale"]),
        ]

    def __str__(self):
        return f"{self.display_name} ({self.locale})"


class PartPrice(models.Model):
    """
    Precios de repuestos por empresa con validez temporal.

    Permite que cada empresa tenga sus propios precios y políticas de impuestos.
    """

    part = models.ForeignKey(
        "taller.Part",  # ✅ String reference (mismo app actualmente, preparar para repuestos.Part en futuro)
        on_delete=models.CASCADE,
        related_name="prices",
        verbose_name=_("Repuesto"),
    )
    company = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="part_prices",
        verbose_name=_("Empresa"),
    )

    # Precio y moneda
    currency = models.CharField(
        _("Moneda"),
        max_length=3,
        default="CLP",
        help_text="Código de moneda ISO 4217 (CLP, USD, BRL, PEN, VES)",
    )
    price = models.DecimalField(
        _("Precio"), max_digits=12, decimal_places=2, help_text="Precio de venta al cliente"
    )

    # Validez temporal
    valid_from = models.DateField(
        _("Válido desde"), help_text="Fecha desde la cual este precio es válido"
    )
    valid_to = models.DateField(
        _("Válido hasta"),
        null=True,
        blank=True,
        help_text="Fecha hasta la cual este precio es válido (null = indefinido)",
    )

    # Política de impuestos
    tax_policy = models.ForeignKey(
        "taller.TaxPolicy",  # ✅ String reference (mismo app actualmente, mover con Part en futuro)
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name=_("Política de Impuestos"),
        help_text="Política de impuestos aplicable a este precio",
    )

    # Metadata
    created_at = models.DateTimeField(_("Fecha de Creación"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Fecha de Actualización"), auto_now=True)

    class Meta:
        verbose_name = _("Precio de Repuesto")
        verbose_name_plural = _("Precios de Repuestos")
        ordering = ["-valid_from"]
        indexes = [
            # ✅ Índice compuesto completo para búsqueda de precios vigentes
            models.Index(
                fields=["company", "part", "valid_from", "valid_to"], name="idx_partprice_lookup"
            ),
            # Índices auxiliares
            models.Index(fields=["part", "valid_from"], name="idx_partprice_part"),
            models.Index(fields=["company", "valid_from"], name="idx_partprice_company"),
        ]
        constraints = [
            # ✅ Constraint para evitar solapes de vigencias en la misma empresa
            # Nota: Django no soporta exclusion constraints nativamente,
            # esto se valida en clean() o con triggers de DB
            # models.CheckConstraint(
            #     check=models.Q(valid_from__lt=models.F('valid_to')) | models.Q(valid_to__isnull=True),
            #     name='partprice_valid_dates'
            # )
        ]

    def __str__(self):
        return f"{self.part.sku}: {self.currency} {self.price}"

    def clean(self):
        """Validar que no haya solapes de vigencias en la misma empresa"""
        from django.core.exceptions import ValidationError

        super().clean()

        if not self.company or not self.part:
            return

        # Buscar precios que se solapen en la misma empresa y part
        overlapping = PartPrice.objects.filter(
            company=self.company, part=self.part, currency=self.currency
        ).exclude(pk=self.pk)

        for price in overlapping:
            # Verificar solapamiento de fechas
            # Caso 1: Nuevo precio empieza durante vigencia de precio existente
            if price.valid_from <= self.valid_from:
                if price.valid_to is None or self.valid_from <= price.valid_to:
                    raise ValidationError(
                        {
                            "valid_from": f"Solapa con precio existente vigente desde {price.valid_from}"
                        }
                    )

            # Caso 2: Nuevo precio termina durante vigencia de precio existente
            if self.valid_to:
                if price.valid_from <= self.valid_to:
                    if price.valid_to is None or self.valid_to <= price.valid_to:
                        raise ValidationError(
                            {
                                "valid_to": f"Solapa con precio existente vigente desde {price.valid_from}"
                            }
                        )

        # Validar que valid_from < valid_to
        if self.valid_to and self.valid_from >= self.valid_to:
            raise ValidationError({"valid_to": "Fecha final debe ser posterior a fecha inicial"})

    @property
    def is_valid(self):
        """Verifica si este precio está vigente hoy"""
        from datetime import date

        today = date.today()
        if today < self.valid_from:
            return False
        if self.valid_to and today > self.valid_to:
            return False
        return True

    @property
    def price_with_tax(self):
        """Precio con impuesto aplicado (si tax_policy existe)"""
        if self.tax_policy and not self.tax_policy.inclusive:
            return self.price * (1 + self.tax_policy.rate)
        return self.price
