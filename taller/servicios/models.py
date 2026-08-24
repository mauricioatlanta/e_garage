from django.db import models

from taller.config.country_settings import CountrySettings

# Countries with active service catalog content. AR, CO, EC, UY are valid Empresa
# tenants but have no catalog data, so they are intentionally excluded here.
_CATALOG_COUNTRY_CODES = ("CL", "US", "MX", "VE", "PE", "BR")


class CategoriaServicio(models.Model):
    """Categoría de servicios por país - identidad estable"""

    COUNTRY_CHOICES = [
        (code, CountrySettings.COUNTRIES[code]["name_es"])
        for code in _CATALOG_COUNTRY_CODES
    ]

    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default="CL")
    code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Código único para reportes/lógica",
    )
    icono = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Nombre del icono (ej: fa-wrench, fa-cog, etc.)",
    )
    orden = models.PositiveIntegerField(
        default=0,
        help_text="Orden de visualización (menor = primero)",
    )
    activo = models.BooleanField(
        default=True,
        help_text="Si está activa y visible",
    )

    class Meta:
        # unique_together = [['country', 'code']]  # Aplicar después de migrar datos
        ordering = ["orden", "code"]
        verbose_name = "Categoría de Servicio"
        verbose_name_plural = "Categorías de Servicios"

    def __str__(self):
        return f"{self.code} ({self.country})"

    def get_label(self, language="es"):
        """Obtiene el nombre localizado con fallback"""
        try:
            name = self.names.get(language=language, is_default=True)
            return name.label
        except CategoriaServicioName.DoesNotExist:
            # Fallback: buscar cualquier nombre en ese idioma
            try:
                name = self.names.filter(language=language).first()
                return name.label if name else self.code
            except:
                return self.code


class CategoriaServicioName(models.Model):
    """Nombres localizados para categorías de servicios"""

    LANGUAGE_CHOICES = [
        ("es", "Español"),
        ("en", "English"),
        ("pt", "Português"),
    ]

    categoria = models.ForeignKey(CategoriaServicio, on_delete=models.CASCADE, related_name="names")
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    label = models.CharField(max_length=100, help_text="Nombre canónico en este idioma")
    aliases = models.JSONField(default=list, blank=True, help_text="Lista de sinónimos/slang")
    is_default = models.BooleanField(default=False, help_text="Nombre principal para este idioma")

    class Meta:
        unique_together = [["categoria", "language", "is_default"]]
        verbose_name = "Nombre de Categoría"
        verbose_name_plural = "Nombres de Categorías"

    def __str__(self):
        return f"{self.label} ({self.language})"


class SubcategoriaServicio(models.Model):
    """Subcategoría de servicios por país"""

    categoria = models.ForeignKey(
        CategoriaServicio, on_delete=models.CASCADE, related_name="subcategorias"
    )
    country = models.CharField(
        max_length=2, choices=CategoriaServicio.COUNTRY_CHOICES, default="CL"
    )
    code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Código único para reportes/lógica",
    )

    orden = models.PositiveIntegerField(
        default=0,
        help_text="Orden de visualización (menor = primero)",
    )
    activo = models.BooleanField(
        default=True,
        help_text="Si está activa y visible",
    )

    class Meta:
        # unique_together = [['country', 'code']]  # Aplicar después de migrar datos
        ordering = ["categoria__orden", "orden", "code"]
        verbose_name = "Subcategoría de Servicio"
        verbose_name_plural = "Subcategorías de Servicios"

    def __str__(self):
        return f"{self.code} ({self.country})"

    def get_label(self, language="es"):
        """Obtiene el nombre localizado con fallback"""
        try:
            name = self.names.get(language=language, is_default=True)
            return name.label
        except SubcategoriaServicioName.DoesNotExist:
            try:
                name = self.names.filter(language=language).first()
                return name.label if name else self.code
            except:
                return self.code

    def save(self, *args, **kwargs):
        # Auto-sincronizar país con categoría padre
        if self.categoria:
            self.country = self.categoria.country
        super().save(*args, **kwargs)


class SubcategoriaServicioName(models.Model):
    """Nombres localizados para subcategorías de servicios"""

    subcategoria = models.ForeignKey(
        SubcategoriaServicio, on_delete=models.CASCADE, related_name="names"
    )
    language = models.CharField(max_length=2, choices=CategoriaServicioName.LANGUAGE_CHOICES)
    label = models.CharField(max_length=100, help_text="Nombre canónico en este idioma")
    aliases = models.JSONField(default=list, blank=True, help_text="Lista de sinónimos/slang")
    is_default = models.BooleanField(default=False, help_text="Nombre principal para este idioma")

    class Meta:
        unique_together = [["subcategoria", "language", "is_default"]]
        verbose_name = "Nombre de Subcategoría"
        verbose_name_plural = "Nombres de Subcategorías"

    def __str__(self):
        return f"{self.label} ({self.language})"


from django.db import models
from django.db.models import Index, UniqueConstraint
from decimal import Decimal

from core.models import TenantScoped

# Definir RUBRO_CHOICES aquí para evitar dependencia circular
# Estos deben coincidir con RUBRO_CHOICES
RUBRO_CHOICES = [
    ("WORKSHOP", "Taller mecánico integral"),
    ("WORKSHOP_MOTO", "Taller de motos"),
    ("WORKSHOP_HEAVY", "Taller de camiones/buses"),
    ("EXHAUST", "Escapes y mufflers"),
    ("PARTS", "Casa de repuestos / Autopartes"),
    ("TIRE", "Vulcanización / Neumáticos y llantas"),
    ("BODYSHOP", "Carrocería / Pintura"),
    ("DETAILING", "Lavado, detailing y estética"),
    ("ELECTRIC", "Electricidad / electrónica automotriz"),
    ("GLASS_AUDIO", "Parabrisas, vidrios y audio / accesorios"),
    ("FLEET", "Mantención de flotas empresariales"),
    ("SUSPENSION_STEERING", "Taller de Suspensión y Dirección"),
    ("BRAKES", "Taller de Frenos"),
    ("OBD_DIAGNOSTIC", "Taller de Diagnóstico Computarizado (OBD-II)"),
    ("CLASSIC_CARS", "Taller de Reparación de Vehículos Clásicos"),
    ("AUDIO_ENTERTAINMENT", "Taller de Sistemas de Audio y Entretenimiento Automotriz"),
    ("GAS_CONVERSION", "Taller de Conversiones a Gas"),
    ("FLEET_REPAIR", "Taller de Reparación de Flotas Corporativas"),
    ("BODY_GLASS", "Taller de Carrocería y Reparación de Vidrios"),
    ("TUNING", "Taller de Tuning / Personalización"),
    ("RECYCLING", "Reciclaje / Chatarra electrónica y catalíticos"),
    ("MIXED", "Mixto (varios rubros)"),
]


class Servicio(TenantScoped):
    """
    Servicio por empresa (tenant-scoped).
    Puede ser un servicio del catálogo o completamente personalizado.
    """

    nombre = models.CharField(max_length=160, db_index=True)
    categoria = models.ForeignKey("CategoriaServicio", on_delete=models.PROTECT, db_index=True)
    subcategoria = models.ForeignKey(
        "SubcategoriaServicio",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_index=True,
    )

    # Campos mejorados según propuesta
    descripcion = models.TextField(
        blank=True,
        default="",
        help_text="Descripción detallada del servicio",
    )
    precio_base = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Precio base del servicio (opcional)",
    )
    duracion_estimada_min = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Duración estimada en minutos",
    )
    codigo_interno = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Código interno del servicio (opcional)",
    )
    rubro_sugerido = models.CharField(
        max_length=30,
        choices=RUBRO_CHOICES,
        blank=True,
        null=True,
        help_text="Rubro donde este servicio es más común",
    )
    rubro_efectivo = models.CharField(
        max_length=30,
        choices=RUBRO_CHOICES,
        blank=True,
        null=True,
        help_text="Rubro efectivo (para empresas MIXED que quieren clasificarlo)",
    )
    activo = models.BooleanField(
        default=True,
        help_text="Si el servicio está activo y disponible",
    )

    class Meta(TenantScoped.Meta):
        indexes = [
            Index(fields=["empresa", "nombre"]),
            Index(fields=["empresa", "categoria"]),
            Index(fields=["empresa", "subcategoria"]),
            Index(fields=["empresa", "activo"]),
            Index(fields=["empresa", "rubro_sugerido"]),
        ]
        ordering = ["categoria__orden", "subcategoria__orden", "nombre"]
        constraints = [
            UniqueConstraint(
                fields=["empresa", "nombre", "categoria"],
                name="uq_servicio_empresa_nombre_categoria",
            ),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.categoria})"

    def get_label(self, language="es"):
        """
        Obtiene el nombre localizado del servicio.
        Fallbacks:
          1. Nombre marcado como is_default para el idioma solicitado.
          2. Primer nombre disponible en ese idioma.
          3. Nombre crudo almacenado en el modelo.
        """
        try:
            return self.names.get(language=language, is_default=True).label
        except ServicioName.DoesNotExist:
            alt = self.names.filter(language=language).first()
            if alt:
                return alt.label
        return self.nombre


class ServicioName(models.Model):
    """Nombres localizados para servicios"""

    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name="names")
    language = models.CharField(max_length=2, choices=CategoriaServicioName.LANGUAGE_CHOICES)
    label = models.CharField(max_length=100, help_text="Nombre canónico en este idioma")
    aliases = models.JSONField(default=list, blank=True, help_text="Lista de sinónimos/slang")
    is_default = models.BooleanField(default=False, help_text="Nombre principal para este idioma")

    class Meta:
        unique_together = [["servicio", "language", "is_default"]]
        verbose_name = "Nombre de Servicio"
        verbose_name_plural = "Nombres de Servicios"

    def __str__(self):
        return f"{self.label} ({self.language})"


class ServicioExterno(TenantScoped):
    """Servicios realizados por empresas externas que el taller puede ofrecer"""

    nombre = models.CharField(
        max_length=160, db_index=True, help_text="Nombre del servicio externo"
    )
    empresa_externa = models.CharField(
        max_length=255, help_text="Nombre de la empresa que realiza el servicio"
    )
    categoria = models.ForeignKey("CategoriaServicio", on_delete=models.PROTECT, db_index=True)
    subcategoria = models.ForeignKey(
        "SubcategoriaServicio",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_index=True,
    )

    # Precios
    costo_taller = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Costo que paga el taller a la empresa externa",
    )
    precio_cliente = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio que cobra el taller al cliente",
    )

    # Información adicional
    descripcion = models.TextField(blank=True, null=True, help_text="Descripción del servicio")
    tiempo_estimado = models.CharField(
        max_length=100, blank=True, null=True, help_text="Tiempo estimado del servicio"
    )
    activo = models.BooleanField(default=True, help_text="Si el servicio está disponible")

    class Meta(TenantScoped.Meta):
        indexes = [
            Index(fields=["empresa", "nombre"]),
            Index(fields=["empresa", "empresa_externa"]),
            Index(fields=["empresa", "categoria"]),
            Index(fields=["empresa", "activo"]),
        ]
        constraints = [
            UniqueConstraint(
                fields=["empresa", "nombre", "empresa_externa"],
                name="uq_servicio_externo_empresa_nombre_proveedor",
            ),
        ]
        verbose_name = "Servicio Externo"
        verbose_name_plural = "Servicios Externos"

    def __str__(self):
        return f"{self.nombre} - {self.empresa_externa}"

    @property
    def ganancia(self):
        """Calcular ganancia por servicio"""
        return self.precio_cliente - self.costo_taller

    @property
    def margen_porcentaje(self):
        """Calcular margen de ganancia en porcentaje"""
        if self.costo_taller > 0:
            return ((self.precio_cliente - self.costo_taller) / self.costo_taller) * 100
        return 0
