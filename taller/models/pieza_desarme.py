"""
Modelo PiezaDesarme: inventario físico de piezas extraídas de vehículos de desarme.
Sigue el patrón multi-tenant canónico (TenantScoped) como Vehiculo y Repuesto.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Index

from core.models import TenantScoped


# Estados de la partida (a nivel de registro completo)
ESTADO_DISPONIBLE = "DISPONIBLE"
ESTADO_RESERVADA = "RESERVADA"
ESTADO_VENDIDA = "VENDIDA"
ESTADO_DANADA = "DANADA"
ESTADO_SCRAP = "SCRAP"
ESTADO_FALTANTE = "FALTANTE"
ESTADO_PIEZA_CHOICES = [
    (ESTADO_DISPONIBLE, "Disponible"),
    (ESTADO_RESERVADA, "Reservada"),
    (ESTADO_VENDIDA, "Vendida"),
    (ESTADO_DANADA, "Dañada"),
    (ESTADO_SCRAP, "Scrap"),
    (ESTADO_FALTANTE, "Faltante"),
]

# Origen del precio (referencia catálogo vs sugerencia sistema vs manual)
ORIGEN_PRECIO_CATALOGO = "CATALOGO"
ORIGEN_PRECIO_MODELO = "MODELO"
ORIGEN_PRECIO_HISTORIAL = "HISTORIAL"
ORIGEN_PRECIO_MANUAL = "MANUAL"
ORIGEN_PRECIO_CHOICES = [
    (ORIGEN_PRECIO_CATALOGO, "Catálogo"),
    (ORIGEN_PRECIO_MODELO, "Modelo / IA"),
    (ORIGEN_PRECIO_HISTORIAL, "Historial"),
    (ORIGEN_PRECIO_MANUAL, "Manual"),
]

# Condición física de la pieza (compartida con Part para el kiosko)
CONDICION_NUEVA = "NUEVO"
CONDICION_EXCELENTE = "EXCELENTE"
CONDICION_BUENA = "BUENA"
CONDICION_REGULAR = "REGULAR"
CONDICION_CHOICES = [
    (CONDICION_NUEVA, "Nuevo"),
    (CONDICION_EXCELENTE, "Excelente"),
    (CONDICION_BUENA, "Buena"),
    (CONDICION_REGULAR, "Regular"),
]


class PiezaDesarme(TenantScoped):
    """
    Partida de piezas extraídas de un vehículo de desarme.
    - Repuesto = catálogo/inventario bodega.
    - PiezaDesarme = unidad física en yarda con trazabilidad por vehículo.
    costo_asignado = costo unitario imputado (por unidad).
    estado_pieza VENDIDA = partida agotada (cantidad llegó a 0).
    """

    vehiculo_desarme = models.ForeignKey(
        "taller.VehiculoDesarme",
        on_delete=models.PROTECT,
        related_name="piezas_desarme",
    )

    repuesto = models.ForeignKey(
        "taller.Repuesto",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="piezas_desarme",
    )
    part = models.ForeignKey(
        "taller.Part",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="piezas_desarme",
    )

    codigo = models.CharField(max_length=100, db_index=True)
    nombre = models.CharField(max_length=255)
    imagen = models.ImageField(
        upload_to="piezas_desarme/",
        null=True,
        blank=True,
        help_text="Foto de la pieza (visible en storefront y kiosko).",
    )
    cantidad = models.PositiveIntegerField(default=1)
    costo_asignado = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Costo unitario imputado (por unidad).",
    )
    precio_venta_sugerido = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Precio base de venta (legado / catálogo). Se mantiene para compatibilidad.",
    )
    # Campos para valorización v4: referencia, sugerencia y trazabilidad
    precio_referencia = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Precio de referencia (catálogo / lista).",
    )
    precio_sugerido = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Precio sugerido por el sistema (modelo / IA / historial).",
    )
    origen_precio = models.CharField(
        max_length=20,
        choices=ORIGEN_PRECIO_CHOICES,
        null=True,
        blank=True,
        db_index=True,
        help_text="Origen del precio actual o de la última sugerencia.",
    )
    prioridad = models.PositiveSmallIntegerField(
        default=0,
        blank=True,
        help_text="Prioridad para ordenar sugerencias o alertas (mayor = más relevante).",
    )
    revisado = models.BooleanField(
        default=False,
        help_text="Indica si el precio fue revisado por un operador.",
    )
    fecha_revision = models.DateTimeField(null=True, blank=True)
    fecha_extraccion = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    publicada = models.BooleanField(
        default=False,
        db_index=True,
        help_text=(
            "Compuerta del kiosko. True = visible en storefront y kiosko. "
            "False = en proceso (confirmada pero no publicada aún)."
        ),
    )

    estado_pieza = models.CharField(
        max_length=20,
        choices=ESTADO_PIEZA_CHOICES,
        default=ESTADO_DISPONIBLE,
        db_index=True,
    )
    condicion = models.CharField(
        max_length=10,
        choices=CONDICION_CHOICES,
        default=CONDICION_BUENA,
        db_index=True,
        help_text="Condición física de la pieza (visible en kiosko y storefront).",
    )
    ubicacion_fisica = models.CharField(max_length=120, null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)
    lado = models.CharField(max_length=50, null=True, blank=True)
    zona = models.CharField(max_length=50, null=True, blank=True)
    posicion = models.CharField(max_length=50, null=True, blank=True)

    def get_label(self, language="es"):
        """
        Nombre localizado (Fase 2 canónico). Usa PiezaDesarmeName si existe; si no, fallback a nombre.
        Mantenido por compatibilidad; preferir get_display_label(empresa, language) para UI.
        """
        return (self.get_catalog_label(language=language) or self.nombre) or ""

    def get_catalog_label(self, language="es"):
        """
        Nombre canónico global por idioma (PiezaDesarmeName).
        Orden: default del idioma solicitado → cualquier del idioma → en → es → self.nombre.
        Devuelve string limpio, nunca None.
        """
        if not hasattr(self, "names"):
            return (self.nombre or "").strip()
        lang = (language or "es")[:2].lower()
        for try_lang in [lang, "en", "es"]:
            try:
                default = self.names.get(language=try_lang, is_default=True)
                if default and default.label:
                    return default.label.strip()
            except self.names.model.DoesNotExist:
                pass
            rec = self.names.filter(language=try_lang).first()
            if rec and rec.label:
                return rec.label.strip()
        return (self.nombre or "").strip()

    def get_company_label(self, empresa, language="es"):
        """
        Nombre visible preferido por empresa e idioma (PiezaDesarmeCompanyLabel).
        Si no existe registro para esa empresa+idioma, devuelve None.
        """
        if empresa is None:
            return None
        if not hasattr(self, "company_labels"):
            return None
        lang = (language or "es")[:2].lower()
        rec = self.company_labels.filter(empresa=empresa, language=lang).first()
        if rec and rec.label:
            return rec.label.strip()
        return None

    def get_display_label(self, empresa=None, language="es"):
        """
        Nombre único para mostrar en UI: prioridad company label → catalog label → self.nombre.
        """
        company = self.get_company_label(empresa=empresa, language=language)
        if company is not None:
            return company
        return self.get_catalog_label(language=language) or (self.nombre or "").strip() or ""

    def get_search_terms(self, empresa=None, language="es"):
        """
        Lista deduplicada de términos para búsqueda: display label, aliases, catalog, código, nombre.
        """
        seen = set()
        result = []
        lang = (language or "es")[:2].lower()

        def add(s):
            if s is None or not isinstance(s, str):
                return
            t = s.strip()
            if t and t.lower() not in seen:
                seen.add(t.lower())
                result.append(t)

        add(self.get_display_label(empresa=empresa, language=language))
        add(self.nombre)
        if self.codigo:
            add(self.codigo)

        if hasattr(self, "company_labels"):
            rec = self.company_labels.filter(empresa=empresa, language=lang).first()
            if rec:
                add(rec.label)
                for a in rec.aliases or []:
                    if isinstance(a, str):
                        add(a)

        if hasattr(self, "names"):
            for name_rec in self.names.filter(language=lang):
                add(name_rec.label)
                for a in name_rec.aliases or []:
                    if isinstance(a, str):
                        add(a)
            for name_rec in self.names.filter(language="en"):
                add(name_rec.label)
                for a in name_rec.aliases or []:
                    if isinstance(a, str):
                        add(a)
            for name_rec in self.names.filter(language="es"):
                add(name_rec.label)
                for a in name_rec.aliases or []:
                    if isinstance(a, str):
                        add(a)

        return result

    def clean(self):
        super().clean()
        if not self.vehiculo_desarme_id:
            return
        # empresa coherente con vehículo
        if self.empresa_id and self.vehiculo_desarme.empresa_id != self.empresa_id:
            raise ValidationError("La pieza y el vehículo deben pertenecer a la misma empresa.")
        # repuesto (si existe) misma empresa
        if self.repuesto_id and self.repuesto.empresa_id != self.empresa_id:
            raise ValidationError("El repuesto referenciado debe pertenecer a la misma empresa.")
        # part: permitir catálogo global (empresa null) o misma empresa
        if (
            self.part_id
            and getattr(self.part, "empresa_id", None) is not None
            and self.part.empresa_id != self.empresa_id
        ):
            raise ValidationError(
                "El part referenciado debe ser de la misma empresa o catálogo global."
            )
        # estado_pieza VENDIDA solo cuando cantidad == 0 (ventas parciales no marcan VENDIDA)
        if self.estado_pieza == ESTADO_VENDIDA and self.cantidad != 0:
            raise ValidationError(
                {"estado_pieza": "Solo se puede marcar como Vendida cuando la cantidad es 0."}
            )

    class Meta(TenantScoped.Meta):
        verbose_name = "Pieza de desarme"
        verbose_name_plural = "Piezas de desarme"
        indexes = [
            Index(fields=["empresa", "vehiculo_desarme"]),
            Index(fields=["empresa", "codigo"]),
            Index(fields=["empresa", "estado_pieza"]),
            Index(fields=["empresa", "publicada", "estado_pieza"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "vehiculo_desarme", "codigo"],
                name="unique_codigo_por_empresa_vehiculo_desarme",
            )
        ]

    def __str__(self):
        return f"{self.nombre} ({self.codigo}) x{self.cantidad} — {self.vehiculo_desarme}"


# Idiomas para nombres canónicos (alineado con servicios)
PIEZA_DESARME_LANGUAGE_CHOICES = [
    ("es", "Español"),
    ("en", "English"),
    ("pt", "Português"),
]


class PiezaDesarmeName(models.Model):
    """
    Nombres localizados y aliases para piezas de desarme (modelo canónico Fase 2).
    Permite búsqueda por slang/sinónimos y múltiples idiomas.
    """

    pieza_desarme = models.ForeignKey(
        PiezaDesarme,
        on_delete=models.CASCADE,
        related_name="names",
    )
    language = models.CharField(max_length=2, choices=PIEZA_DESARME_LANGUAGE_CHOICES)
    label = models.CharField(max_length=255, help_text="Nombre canónico en este idioma")
    aliases = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de sinónimos/slang para búsqueda (ej. ['engine', 'motor'])",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Nombre principal para este idioma (un solo True por pieza+language)",
    )

    class Meta:
        verbose_name = "Nombre de pieza desarme"
        verbose_name_plural = "Nombres de piezas desarme"
        constraints = [
            models.UniqueConstraint(
                fields=["pieza_desarme", "language", "is_default"],
                name="uq_pieza_desarme_name_pieza_lang_default",
            )
        ]

    def __str__(self):
        return f"{self.label} ({self.language})"


class PiezaDesarmeCompanyLabel(models.Model):
    """
    Nombre visible preferido por empresa e idioma para una pieza de desarme.
    Permite que cada empresa defina cómo mostrar el nombre de la pieza en su idioma.
    """

    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="pieza_labels",
    )
    pieza_desarme = models.ForeignKey(
        PiezaDesarme,
        on_delete=models.CASCADE,
        related_name="company_labels",
    )
    language = models.CharField(
        max_length=2,
        choices=PIEZA_DESARME_LANGUAGE_CHOICES,
    )
    label = models.CharField(max_length=255, help_text="Nombre visible para esta empresa e idioma")
    aliases = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de sinónimos/slang para búsqueda",
    )
    is_preferred = models.BooleanField(
        default=True,
        help_text="Si es el nombre preferido para mostrar en este idioma",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Nombre de pieza desarme por empresa"
        verbose_name_plural = "Nombres de piezas desarme por empresa"
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "pieza_desarme", "language"],
                name="uq_pieza_desarme_company_label_empresa_pieza_lang",
            )
        ]

    def __str__(self):
        return f"{self.label} ({self.language}) — {self.empresa_id}"


# Tipos de evento para historial de precios (v4)
TIPO_EVENTO_VALORIZACION = "VALORIZACION"
TIPO_EVENTO_VENTA = "VENTA"
TIPO_EVENTO_AJUSTE = "AJUSTE"
TIPO_EVENTO_HISTORICO_CHOICES = [
    (TIPO_EVENTO_VALORIZACION, "Valorización"),
    (TIPO_EVENTO_VENTA, "Venta"),
    (TIPO_EVENTO_AJUSTE, "Ajuste"),
]


class PrecioHistoricoPieza(models.Model):
    """
    Historial de precios para piezas de desarme (v4).
    Permite trazabilidad y alimentar sugerencias de valorización.
    """

    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        db_index=True,
        related_name="precios_historicos_pieza",
    )
    pieza_desarme = models.ForeignKey(
        PiezaDesarme,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historial_precios",
    )
    vehiculo_desarme = models.ForeignKey(
        "taller.VehiculoDesarme",
        on_delete=models.CASCADE,
        related_name="precios_historicos_pieza",
        help_text="Vehículo de origen (contexto del precio).",
    )
    codigo = models.CharField(max_length=100, db_index=True)
    nombre = models.CharField(max_length=255)
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=150, blank=True)
    anio = models.PositiveIntegerField(null=True, blank=True)
    precio = models.DecimalField(max_digits=12, decimal_places=2)
    tipo_evento = models.CharField(
        max_length=20,
        choices=TIPO_EVENTO_HISTORICO_CHOICES,
        db_index=True,
    )
    origen_precio = models.CharField(
        max_length=20,
        choices=ORIGEN_PRECIO_CHOICES,
        null=True,
        blank=True,
        db_index=True,
    )
    fecha = models.DateTimeField(db_index=True)

    class Meta:
        verbose_name = "Precio histórico pieza"
        verbose_name_plural = "Precios históricos pieza"
        ordering = ["-fecha"]
        indexes = [
            Index(fields=["empresa", "fecha"]),
            Index(fields=["empresa", "tipo_evento"]),
            Index(fields=["pieza_desarme", "fecha"]),
        ]

    def __str__(self):
        return f"{self.codigo} {self.precio} ({self.tipo_evento}) @ {self.fecha}"
