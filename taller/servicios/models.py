import json

from django.db import models

from taller.models.documento import Documento


class CategoriaServicio(models.Model):
    """Categoría de servicios por país - identidad estable"""

    COUNTRY_CHOICES = [
        ("CL", "Chile"),
        ("US", "Estados Unidos"),
    ]

    country = models.CharField(max_length=2, choices=COUNTRY_CHOICES, default="CL")
    code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Código único para reportes/lógica",
    )

    class Meta:
        # unique_together = [['country', 'code']]  # Aplicar después de migrar datos
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
    ]

    categoria = models.ForeignKey(
        CategoriaServicio, on_delete=models.CASCADE, related_name="names"
    )
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    label = models.CharField(max_length=100, help_text="Nombre canónico en este idioma")
    aliases = models.JSONField(
        default=list, blank=True, help_text="Lista de sinónimos/slang"
    )
    is_default = models.BooleanField(
        default=False, help_text="Nombre principal para este idioma"
    )

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

    class Meta:
        # unique_together = [['country', 'code']]  # Aplicar después de migrar datos
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
    language = models.CharField(
        max_length=2, choices=CategoriaServicioName.LANGUAGE_CHOICES
    )
    label = models.CharField(max_length=100, help_text="Nombre canónico en este idioma")
    aliases = models.JSONField(
        default=list, blank=True, help_text="Lista de sinónimos/slang"
    )
    is_default = models.BooleanField(
        default=False, help_text="Nombre principal para este idioma"
    )

    class Meta:
        unique_together = [["subcategoria", "language", "is_default"]]
        verbose_name = "Nombre de Subcategoría"
        verbose_name_plural = "Nombres de Subcategorías"

    def __str__(self):
        return f"{self.label} ({self.language})"


from django.db import models
from django.db.models import Index, UniqueConstraint

from core.models import TenantScoped


class Servicio(TenantScoped):
    nombre = models.CharField(max_length=160, db_index=True)
    categoria = models.ForeignKey(
        "CategoriaServicio", on_delete=models.PROTECT, db_index=True
    )
    subcategoria = models.ForeignKey(
        "SubcategoriaServicio",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta(TenantScoped.Meta):
        indexes = [
            Index(fields=["empresa", "nombre"]),
            Index(fields=["empresa", "categoria"]),
            Index(fields=["empresa", "subcategoria"]),
        ]
        constraints = [
            UniqueConstraint(
                fields=["empresa", "nombre", "categoria"],
                name="uq_servicio_empresa_nombre_categoria",
            ),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.categoria})"


class ServicioName(models.Model):
    """Nombres localizados para servicios"""

    servicio = models.ForeignKey(
        Servicio, on_delete=models.CASCADE, related_name="names"
    )
    language = models.CharField(
        max_length=2, choices=CategoriaServicioName.LANGUAGE_CHOICES
    )
    label = models.CharField(max_length=100, help_text="Nombre canónico en este idioma")
    aliases = models.JSONField(
        default=list, blank=True, help_text="Lista de sinónimos/slang"
    )
    is_default = models.BooleanField(
        default=False, help_text="Nombre principal para este idioma"
    )

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
    categoria = models.ForeignKey(
        "CategoriaServicio", on_delete=models.PROTECT, db_index=True
    )
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
    descripcion = models.TextField(
        blank=True, null=True, help_text="Descripción del servicio"
    )
    tiempo_estimado = models.CharField(
        max_length=100, blank=True, null=True, help_text="Tiempo estimado del servicio"
    )
    activo = models.BooleanField(
        default=True, help_text="Si el servicio está disponible"
    )

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
