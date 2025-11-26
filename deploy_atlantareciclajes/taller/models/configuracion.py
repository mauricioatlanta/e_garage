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
    # Campo legacy de dirección (deprecar progresivamente)
    direccion = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="Dirección",
        help_text="[LEGACY] Dirección de texto plano - Usar legal_address en su lugar",
    )

    # Nueva dirección estructurada usando modelo Address
    legal_address = models.ForeignKey(
        "ubicacion.Address",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="company_legal_addresses",
        verbose_name="Dirección Legal",
        help_text="Dirección legal/fiscal de la empresa (estructurada con ciudad, estado, país)",
    )

    # Feature flag para rollout gradual de Address v2
    use_address_v2 = models.BooleanField(
        default=False,
        verbose_name="Usar Address v2",
        help_text="Activar para usar el nuevo sistema de direcciones estructuradas (Address). "
        "Desactivar para seguir usando campos legacy (direccion, region, ciudad).",
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
        if not getattr(self, "empresa", None):
            return "Configuración sin empresa"

        nombre_empresa = (
            self.nombre_publico
            or getattr(self.empresa, "nombre_taller", "")
            or getattr(self.empresa, "empresa", "")
            or "sin nombre"
        )
        return f"Config {self.empresa_id} – {nombre_empresa}"

    class Meta:
        verbose_name = "Configuración de Empresa"
        verbose_name_plural = "Configuraciones de Empresas"

    def save(self, *args, **kwargs):
        # Normalización automática de moneda según país
        if not self.moneda and hasattr(self, "empresa") and self.empresa:
            self.moneda = "CLP" if getattr(self.empresa, "pais", "CL") == "CL" else "USD"
        super().save(*args, **kwargs)
