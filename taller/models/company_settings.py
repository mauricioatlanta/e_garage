import os

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from PIL import Image


def validate_logo_size(image):
    """Valida que el logo tenga dimensiones apropiadas"""
    if image:
        img = Image.open(image)
        width, height = img.size

        # Máximo 1000x1000 px
        if width > 1000 or height > 1000:
            raise ValidationError("El logo debe ser menor a 1000x1000 píxeles")

        # Mínimo 100x100 px
        if width < 100 or height < 100:
            raise ValidationError("El logo debe ser mayor a 100x100 píxeles")

        # Máximo 2MB
        if image.size > 2 * 1024 * 1024:
            raise ValidationError("El logo debe ser menor a 2MB")


class CompanySettings(models.Model):
    """Configuración de branding y datos de empresa por suscriptor"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="company_settings",
        help_text="Usuario propietario de la configuración",
    )

    # === INFORMACIÓN BÁSICA ===
    company_name = models.CharField(
        max_length=255,
        verbose_name="Nombre de la empresa",
        help_text="Nombre que aparecerá en lugar de 'eGarage'",
    )

    tagline = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Eslogan",
        help_text="Texto corto que aparece bajo el nombre (ej: 'Tu taller de confianza')",
    )

    # === BRANDING VISUAL ===
    logo = models.ImageField(
        upload_to="company_logos/",
        null=True,
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["png", "jpg", "jpeg", "svg"]),
            validate_logo_size,
        ],
        verbose_name="Logo de la empresa",
        help_text="Logo personalizado (máx. 1000x1000px, 2MB). Formatos: PNG, JPG, SVG",
    )

    primary_color = models.CharField(
        max_length=7,
        default="#0d6efd",
        verbose_name="Color primario",
        help_text="Color principal del tema (formato hexadecimal, ej: #FF0000)",
    )

    secondary_color = models.CharField(
        max_length=7,
        default="#6c757d",
        verbose_name="Color secundario",
        help_text="Color secundario del tema (formato hexadecimal)",
    )

    # === DATOS DE CONTACTO ===
    address = models.TextField(
        blank=True, verbose_name="Dirección", help_text="Dirección completa del taller"
    )

    phone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Teléfono",
        help_text="Teléfono principal",
    )

    email = models.EmailField(
        blank=True, verbose_name="Email", help_text="Email de contacto"
    )

    website = models.URLField(
        blank=True, verbose_name="Sitio web", help_text="URL del sitio web (opcional)"
    )

    # === INFORMACIÓN FISCAL ===
    tax_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="RUT/NIT/Tax ID",
        help_text="Número de identificación fiscal",
    )

    business_license = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Licencia comercial",
        help_text="Número de licencia o registro comercial",
    )

    # === CONFIGURACIÓN REGIONAL ===
    currency = models.CharField(
        max_length=3,
        default="CLP",
        choices=[
            ("CLP", "Peso Chileno (CLP)"),
            ("USD", "Dólar Estadounidense (USD)"),
            ("EUR", "Euro (EUR)"),
            ("MXN", "Peso Mexicano (MXN)"),
        ],
        verbose_name="Moneda",
        help_text="Moneda utilizada en los documentos",
    )

    timezone = models.CharField(
        max_length=50,
        default="America/Santiago",
        verbose_name="Zona horaria",
        help_text="Zona horaria para fechas y horas",
    )

    # === CONFIGURACIÓN DE DOCUMENTOS ===
    invoice_prefix = models.CharField(
        max_length=10,
        default="FAC",
        verbose_name="Prefijo de facturas",
        help_text="Prefijo para numeración de facturas (ej: FAC-001)",
    )

    quote_prefix = models.CharField(
        max_length=10,
        default="COT",
        verbose_name="Prefijo de cotizaciones",
        help_text="Prefijo para numeración de cotizaciones (ej: COT-001)",
    )

    work_order_prefix = models.CharField(
        max_length=10,
        default="OT",
        verbose_name="Prefijo de órdenes de trabajo",
        help_text="Prefijo para numeración de órdenes (ej: OT-001)",
    )

    # === INFORMACIÓN ADICIONAL ===
    about_text = models.TextField(
        blank=True,
        verbose_name="Acerca de nosotros",
        help_text="Texto descriptivo de la empresa (aparece en documentos y página principal)",
    )

    terms_and_conditions = models.TextField(
        blank=True,
        verbose_name="Términos y condiciones",
        help_text="Términos que aparecen en contratos y documentos",
    )

    # === METADATA ===
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración de Empresa"
        verbose_name_plural = "Configuraciones de Empresas"

    def __str__(self):
        return f"Configuración de {self.company_name} ({self.user.username})"

    def get_logo_url(self):
        """Retorna URL del logo personalizado o el por defecto"""
        if self.logo:
            return self.logo.url
        return "/static/images/egarage_default_logo.png"

    def get_company_name(self):
        """Retorna nombre personalizado o 'eGarage' por defecto"""
        return self.company_name or "eGarage"

    def get_primary_color(self):
        """Retorna color primario con fallback"""
        return self.primary_color or "#0d6efd"

    def get_secondary_color(self):
        """Retorna color secundario con fallback"""
        return self.secondary_color or "#6c757d"

    def save(self, *args, **kwargs):
        # Validar colores hexadecimales
        if self.primary_color and not self.primary_color.startswith("#"):
            self.primary_color = f"#{self.primary_color}"
        if self.secondary_color and not self.secondary_color.startswith("#"):
            self.secondary_color = f"#{self.secondary_color}"

        super().save(*args, **kwargs)

        # Redimensionar logo si es necesario
        if self.logo:
            self._resize_logo()

    def _resize_logo(self):
        """Redimensiona el logo si excede las dimensiones máximas"""
        try:
            img = Image.open(self.logo.path)
            if img.height > 400 or img.width > 400:
                # Mantener proporción, máximo 400px en cualquier dimensión
                img.thumbnail((400, 400), Image.Resampling.LANCZOS)
                img.save(self.logo.path)
        except Exception:
            # Si falla el redimensionamiento, continúa sin error
            pass


class CompanySettingsHistory(models.Model):
    """Historial de cambios en configuración de empresa"""

    company_settings = models.ForeignKey(
        CompanySettings, on_delete=models.CASCADE, related_name="history"
    )

    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    changed_at = models.DateTimeField(auto_now_add=True)

    field_changed = models.CharField(max_length=100)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)

    class Meta:
        verbose_name = "Historial de Configuración"
        verbose_name_plural = "Historiales de Configuración"
        ordering = ["-changed_at"]
        app_label = "taller"

    def __str__(self):
        return f"{self.company_settings.company_name} - {self.field_changed} ({self.changed_at})"
