from decimal import Decimal

from django.db import models


class ConfiguracionEmpresa(models.Model):
    empresa = models.OneToOneField(
        "taller.Empresa", on_delete=models.CASCADE, related_name="config"
    )
    nombre_publico = models.CharField(max_length=150, blank=True, default="")
    tagline = models.CharField(
        max_length=180,
        blank=True,
        default="",
        verbose_name="Eslogan",
        help_text="Texto corto que aparece bajo el nombre",
    )
    logo = models.ImageField(upload_to="logos/", null=True, blank=True)

    # —— CAMPOS DE CONTACTO ——
    direccion = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="Dirección",
        help_text="Dirección completa de la empresa",
    )
    telefono = models.CharField(
        max_length=40,
        blank=True,
        default="",
        verbose_name="Teléfono",
        help_text="Número de teléfono de contacto (E.164 opcional)",
    )
    email_contacto = models.EmailField(
        blank=True,
        default="",
        verbose_name="Correo Electrónico",
        help_text="Correo electrónico de contacto",
    )
    sitio_web = models.URLField(
        blank=True,
        default="",
        verbose_name="Sitio Web",
        help_text="URL del sitio web de la empresa",
    )

    # —— IMPUESTOS / MONEDA ——
    moneda = models.CharField(max_length=10, default="CLP")  # CLP / USD
    tasa_impuesto = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("19.00"),
        verbose_name="Tasa de Impuesto",
        help_text="IVA/Sales tax %",
    )
    aplicar_impuesto_por_defecto = models.BooleanField(
        default=False,
        verbose_name="Aplicar impuesto por defecto",
        help_text="Aplicar IVA/impuesto automáticamente",
    )

    # —— VISUAL / FLAGS ——
    brand_color = models.CharField(
        max_length=7,
        default="#1a202c",
        verbose_name="Color de Marca",
        help_text="Color principal de la marca (hex)",
    )
    dividir_por_tecnico = models.BooleanField(
        default=False,
        verbose_name="Dividir por técnico",
        help_text="Separar trabajos por técnico asignado",
    )

    # —— TÉCNICO POR DEFECTO (mantener compatibilidad) ——
    tecnico_por_defecto = models.ForeignKey(
        "taller.Tecnico",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tecnico_por_defecto_de",
    )

    # Auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"Config {self.empresa_id} – {self.nombre_publico or self.empresa.nombre}"
            if getattr(self, "empresa", None)
            else "Configuración sin empresa"
        )

    class Meta:
        verbose_name = "Configuración de Empresa"
        verbose_name_plural = "Configuraciones de Empresas"

    def save(self, *args, **kwargs):
        # Normalización automática de moneda según país
        if not self.moneda and hasattr(self, "empresa") and self.empresa:
            self.moneda = (
                "CLP" if getattr(self.empresa, "pais", "CL") == "CL" else "USD"
            )
        super().save(*args, **kwargs)
