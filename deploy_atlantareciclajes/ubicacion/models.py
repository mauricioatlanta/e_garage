from django.db import models
from django.utils.translation import gettext_lazy as _


class Estado(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre


class Ciudad(models.Model):
    nombre = models.CharField(max_length=100)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE)
    zip_code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.nombre}, {self.estado}"


class Address(models.Model):
    """
    Dirección genérica para Company/Client (multi-país).
    Usa Ciudad de taller.models.ubicacion → Estado → pais (en Estado.pais).

    Nota: Este modelo usa Ciudad de 'taller.Ciudad' (modelo mejorado con soporte multi-país)
    no el Ciudad de esta app que es más simple y legacy.

    Convenciones del proyecto:
    - FK como string ('app.Model') para lazy references
    - Reutiliza Estado/Ciudad existentes de taller
    - Soporta billing/shipping addresses
    """

    # FK opcional a empresa (para direcciones de empresa)
    company = models.ForeignKey(
        "taller.Empresa",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="addresses",
        help_text="Empresa propietaria de esta dirección (opcional)",
    )

    # Dirección
    line1 = models.CharField(
        _("Dirección Línea 1"), max_length=160, help_text="Calle, número, edificio, etc."
    )
    line2 = models.CharField(
        _("Dirección Línea 2"),
        max_length=160,
        blank=True,
        default="",
        help_text="Apartamento, suite, unidad, etc. (opcional)",
    )

    # Ciudad (usa el modelo mejorado de taller con soporte multi-país)
    city = models.ForeignKey(
        "taller.Ciudad",  # Referencia al modelo mejorado en taller/models/ubicacion.py
        on_delete=models.PROTECT,
        related_name="addresses",
        verbose_name=_("Ciudad"),
        help_text="Ciudad (incluye estado y país)",
    )

    # Código postal (Zipcode/CEP/Código Postal)
    postal_code = models.CharField(
        _("Código Postal"),
        max_length=20,
        blank=True,
        default="",
        help_text="Zipcode (US), CEP (BR), Código Postal (VE/PE/CL)",
    )

    # Coordenadas geográficas (opcional para mapas/delivery)
    latitude = models.DecimalField(
        _("Latitud"),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Coordenada geográfica (opcional)",
    )
    longitude = models.DecimalField(
        _("Longitud"),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Coordenada geográfica (opcional)",
    )

    # Metadata
    created_at = models.DateTimeField(_("Fecha de Creación"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Fecha de Actualización"), auto_now=True)

    class Meta:
        verbose_name = _("Dirección")
        verbose_name_plural = _("Direcciones")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["city"]),
            models.Index(fields=["company"]),
            models.Index(fields=["postal_code"]),
        ]

    def __str__(self):
        """Representación legible de la dirección"""
        if self.line2:
            return f"{self.line1}, {self.line2}, {self.city}"
        return f"{self.line1}, {self.city}"

    @property
    def full_address(self):
        """Dirección completa con ciudad, estado y país"""
        parts = [self.line1]
        if self.line2:
            parts.append(self.line2)
        parts.append(str(self.city.nombre))
        parts.append(str(self.city.estado.nombre))
        parts.append(self.city.estado.get_pais_display())
        if self.postal_code:
            parts.append(self.postal_code)
        return ", ".join(parts)

    @property
    def country_code(self):
        """Código de país de esta dirección"""
        return self.city.estado.pais

    @property
    def state(self):
        """Estado/Departamento de esta dirección"""
        return self.city.estado

    # NOTA: Sales tax NO se calcula aquí
    # La tasa de impuestos correcta viene de TaxPolicy vía resolve_tax_rate()
    # que considera: país, estado, ciudad, y tipo de item (parts/services/both)
    # Ver: taller/impuestos/engine.py
