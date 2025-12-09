# -*- coding: utf-8 -*-
"""
Catálogo de Servicios con I18N y precios multi-empresa

Convenciones del proyecto:
- FKs como string ('app.Model') para lazy references
- Internacionalización con tablas separadas (*I18N)
- Precios por empresa con validez temporal
- Reutiliza TaxPolicy de catalogo_repuestos
"""
from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _


class Service(models.Model):
    """
    Servicio en el catálogo (multi-empresa).

    Cada empresa puede tener sus propios servicios, o usar catálogo compartido.
    Los nombres se manejan vía ServiceI18N para internacionalización.

    Convenciones:
    - FKs como string ('app.Model')
    - I18N con tabla separada
    - Precios por empresa (ServicePrice)
    """

    # Multi-tenant: empresa opcional (null = catálogo global)
    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="services_catalog",
        null=True,
        blank=True,
        help_text="Empresa propietaria (null = catálogo global compartido)",
    )

    # Identificación
    code = models.CharField(
        _("Código"),
        max_length=64,
        unique=True,
        db_index=True,  # ✅ Índice para búsquedas rápidas por código
        help_text="Código único del servicio (ej: OIL_CHANGE, BRAKE_SERVICE)",
    )
    category = models.CharField(
        _("Categoría"),
        max_length=64,
        help_text="Categoría del servicio (ej: maintenance, repair, diagnostic)",
    )

    # Horas estándar (opcional)
    std_hours = models.DecimalField(
        _("Horas Estándar"),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Tiempo estimado en horas (opcional)",
    )

    # Status
    active = models.BooleanField(
        _("Activo"), default=True, help_text="Si el servicio está disponible"
    )

    # Metadata
    created_at = models.DateTimeField(_("Fecha de Creación"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Fecha de Actualización"), auto_now=True)

    class Meta:
        verbose_name = _("Servicio de Catálogo")
        verbose_name_plural = _("Servicios de Catálogo")
        ordering = ["code"]
        indexes = [
            models.Index(fields=["empresa", "code"]),
            models.Index(fields=["empresa", "category"]),
            models.Index(fields=["active"]),
        ]

    def __str__(self):
        return self.code

    def get_display_name(self, locale="es-CL"):
        """
        Obtener nombre localizado del servicio con fallback inteligente.

        Estrategia de fallback:
        1. Buscar locale exacto (ej: es-PE)
        2. Fallback a es-CL (idioma por defecto del sistema)
        3. Fallback al primer I18N disponible
        4. Fallback al code si no hay I18N

        Args:
            locale (str): Código de locale (ej: 'es-CL', 'en-US', 'pt-BR')

        Returns:
            str: Nombre localizado o code como fallback

        Ejemplos:
            >>> service.get_display_name('es-CL')  # Exacto
            'Cambio de Aceite'
            >>> service.get_display_name('es-PE')  # Fallback a es-CL
            'Cambio de Aceite'
            >>> service.get_display_name('fr-FR')  # Fallback a primer disponible
            'Cambio de Aceite'
        """
        # 1. Intentar locale exacto
        try:
            i18n = self.i18n_catalog.get(locale=locale)
            return i18n.display_name
        except ServiceI18N.DoesNotExist:
            pass

        # 2. Fallback a es-CL (idioma por defecto)
        if locale != "es-CL":
            try:
                i18n = self.i18n_catalog.get(locale="es-CL")
                return i18n.display_name
            except ServiceI18N.DoesNotExist:
                pass

        # 3. Fallback al primer I18N disponible
        i18n = self.i18n_catalog.first()
        if i18n:
            return i18n.display_name

        # 4. Fallback al code
        return self.code

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
            ServicePrice or None: Registro de precio vigente, o None si no existe

        Ejemplos:
            >>> price = service.get_price(empresa)
            >>> if price:
            ...     print(f"{price.currency} {price.price}")
            'CLP 45000'

            >>> price = service.get_price(empresa, date(2025, 6, 15))
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


class ServiceI18N(models.Model):
    """
    Nombres localizados para servicios (I18N).

    Permite tener nombres diferentes por país/idioma:
    - es-CL: "Cambio de Aceite"
    - en-US: "Oil Change"
    - pt-BR: "Troca de Óleo"
    - es-PE: "Cambio de Aceite"
    - es-VE: "Cambio de Aceite"
    """

    service = models.ForeignKey(
        "taller.Service",  # ✅ String reference (mismo app actualmente, mover a servicios en futuro)
        on_delete=models.CASCADE,
        related_name="i18n_catalog",
        verbose_name=_("Servicio"),
    )
    locale = models.CharField(
        _("Locale"),
        max_length=8,
        help_text="Código de idioma-país (ej: es-CL, en-US, pt-BR, es-PE, es-VE)",
    )
    display_name = models.CharField(
        _("Nombre para Mostrar"), max_length=160, help_text="Nombre del servicio en este idioma"
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
        verbose_name = _("Nombre de Servicio (I18N)")
        verbose_name_plural = _("Nombres de Servicios (I18N)")
        unique_together = ("service", "locale")
        indexes = [
            models.Index(fields=["service", "locale"]),
            models.Index(fields=["locale"]),
        ]

    def __str__(self):
        return f"{self.display_name} ({self.locale})"


class ServicePrice(models.Model):
    """
    Precios de servicios por empresa con validez temporal.

    Permite que cada empresa tenga sus propios precios y políticas de impuestos.
    """

    service = models.ForeignKey(
        "taller.Service",  # ✅ String reference (mismo app actualmente, mover a servicios en futuro)
        on_delete=models.CASCADE,
        related_name="prices",
        verbose_name=_("Servicio"),
    )
    company = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="service_prices",
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
        "taller.TaxPolicy",  # ✅ String reference (mismo app actualmente, TaxPolicy está con Part)
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
        verbose_name = _("Precio de Servicio")
        verbose_name_plural = _("Precios de Servicios")
        ordering = ["-valid_from"]
        indexes = [
            # ✅ Índice compuesto completo para búsqueda de precios vigentes
            models.Index(
                fields=["company", "service", "valid_from", "valid_to"],
                name="idx_serviceprice_lookup",
            ),
            # Índices auxiliares
            models.Index(fields=["service", "valid_from"], name="idx_serviceprice_service"),
            models.Index(fields=["company", "valid_from"], name="idx_serviceprice_company"),
        ]
        constraints = [
            # ✅ Constraint para evitar solapes de vigencias en la misma empresa
            # Nota: Django no soporta exclusion constraints nativamente,
            # esto se valida en clean() o con triggers de DB
        ]

    def __str__(self):
        return f"{self.service.code}: {self.currency} {self.price}"

    def clean(self):
        """Validar que no haya solapes de vigencias en la misma empresa"""
        from django.core.exceptions import ValidationError

        super().clean()

        if not self.company or not self.service:
            return

        # Buscar precios que se solapen en la misma empresa y service
        overlapping = ServicePrice.objects.filter(
            company=self.company, service=self.service, currency=self.currency
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
