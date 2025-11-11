from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class Estado(models.Model):
    """
    Modelo para estados/provincias/departamentos/regiones.

    Normalización:
    - pais: ISO 3166-1 alpha-2 (CL, US, BR, PE, VE)
    - codigo: Código de estado consistente (GA, SP, RM, LIM, etc.)
    - unique_together: (pais, codigo) para evitar duplicados

    Ejemplos:
    - USA: GA, CA, NY, FL, TX
    - Brasil: SP, RJ, MG, BA
    - Chile: RM, VAL, BIO
    - Perú: LIM, ARE, CUS
    - Venezuela: DC, ZUL, CAR
    """

    nombre = models.CharField(_("Nombre"), max_length=100)
    codigo = models.CharField(
        _("Código"),
        max_length=10,  # Aumentado a 10 para códigos más largos
        help_text="Código del estado (GA, SP, RM, LIM, etc.) - Único por país",
    )
    pais = models.CharField(
        _("País"),
        max_length=2,  # ISO 3166-1 alpha-2
        choices=[
            ("CL", "Chile"),  # ISO 3166-1: CL
            ("US", "Estados Unidos"),  # ISO 3166-1: US
            ("BR", "Brasil"),  # ISO 3166-1: BR
            ("PE", "Perú"),  # ISO 3166-1: PE
            ("VE", "Venezuela"),  # ISO 3166-1: VE
        ],
        help_text="Código de país ISO 3166-1 alpha-2",
    )
    sales_tax = models.DecimalField(
        _("Sales Tax / ICMS (%)"), max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    timezone = models.CharField(_("Zona Horaria"), max_length=50, default="America/New_York")
    # Campos adicionales para Brasil
    codigo_ibge = models.CharField(
        _("Código IBGE"), max_length=2, null=True, blank=True, help_text="Para Brasil"
    )
    # Campos adicionales (nombre en portugués, etc.)
    nome = models.CharField(
        _("Nome"), max_length=100, null=True, blank=True, help_text="Nome em português"
    )
    sigla = models.CharField(
        _("Sigla"), max_length=5, null=True, blank=True, help_text="Sigla do estado (BR)"
    )

    class Meta:
        verbose_name = _("Estado")
        verbose_name_plural = _("Estados")
        ordering = ["pais", "nombre"]
        unique_together = [("pais", "codigo")]  # ✅ ISO 3166-1 alpha-2 + código de estado
        indexes = [
            models.Index(fields=["pais", "codigo"], name="idx_estado_pais_codigo"),
            models.Index(fields=["pais"], name="idx_estado_pais"),
        ]

    def clean(self):
        """Validar normalización ISO 3166-1 alpha-2 y código consistente"""
        super().clean()

        # Validar pais es ISO 3166-1 alpha-2 (2 caracteres uppercase)
        if self.pais:
            if len(self.pais) != 2:
                raise ValidationError(
                    {"pais": "País debe ser código ISO 3166-1 alpha-2 (2 caracteres)"}
                )
            self.pais = self.pais.upper()

        # Validar codigo es consistente (uppercase, sin espacios)
        if self.codigo:
            self.codigo = self.codigo.upper().strip()
            if len(self.codigo) > 10:
                raise ValidationError({"codigo": "Código de estado no puede exceder 10 caracteres"})

    def save(self, *args, **kwargs):
        """Ejecutar validación antes de guardar"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.codigo}) - {self.get_pais_display()}"


class Ciudad(models.Model):
    """
    Modelo para ciudades principales (USA, Brasil, Chile, etc.)

    Normalización:
    - nombre: Nombre de la ciudad
    - estado: FK a Estado (con pais)
    - unique_together: (estado, nombre) para evitar duplicados en el mismo estado
    - Índices optimizados para queries por estado

    Ejemplos:
    - Lima, LIM (Perú)
    - São Paulo, SP (Brasil)
    - Santiago, RM (Chile)
    - Los Angeles, CA (USA)
    - Caracas, DC (Venezuela)
    """

    nombre = models.CharField(_("Nombre"), max_length=100)
    estado = models.ForeignKey(
        "taller.Estado", on_delete=models.CASCADE, related_name="ciudades"  # ✅ FK como string
    )
    poblacion = models.IntegerField(_("Población"), null=True, blank=True)
    es_capital = models.BooleanField(_("Es Capital"), default=False)
    latitud = models.DecimalField(
        _("Latitud"), max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitud = models.DecimalField(
        _("Longitud"), max_digits=9, decimal_places=6, null=True, blank=True
    )
    # Sales tax local adicional (se suma al del estado)
    sales_tax_local = models.DecimalField(
        _("Sales Tax Local / ISS (%)"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    # Campos adicionales para Brasil
    codigo_ibge = models.CharField(
        _("Código IBGE"), max_length=7, null=True, blank=True, help_text="Para Brasil"
    )
    nome = models.CharField(
        _("Nome"), max_length=100, null=True, blank=True, help_text="Nome em português"
    )

    class Meta:
        verbose_name = _("Ciudad")
        verbose_name_plural = _("Ciudades")
        ordering = ["estado__pais", "estado__nombre", "nombre"]
        unique_together = [("estado", "nombre")]  # ✅ Una ciudad por nombre en cada estado
        indexes = [
            models.Index(fields=["estado", "nombre"], name="idx_ciudad_estado_nombre"),
            models.Index(fields=["estado"], name="idx_ciudad_estado"),
        ]
        db_table = "taller_ciudad_usa"  # Evitar conflicto con TallerCiudad existente

    def clean(self):
        """Validar consistencia de ciudad"""
        super().clean()

        # Normalizar nombre (capitalizar primera letra de cada palabra)
        if self.nombre:
            self.nombre = self.nombre.strip()

    def save(self, *args, **kwargs):
        """Ejecutar validación antes de guardar"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre}, {self.estado.codigo}"

    @property
    def nombre_completo(self):
        return f"{self.nombre}, {self.estado.nombre}"

    @property
    def sales_tax_total(self):
        """Sales tax total (estado + local) / ICMS + ISS"""
        return self.estado.sales_tax + self.sales_tax_local
