from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from taller.models.mixins import AuditMixin

User = get_user_model()

ZONAS_VEHICULO = [
    ("capo", _("Capó")),
    ("techo", _("Techo")),
    ("maletero", _("Maletero")),
    ("puerta_di", _("Puerta delantera izquierda")),
    ("puerta_dd", _("Puerta delantera derecha")),
    ("puerta_ti", _("Puerta trasera izquierda")),
    ("puerta_td", _("Puerta trasera derecha")),
    ("parachoque_del", _("Paragolpe delantero")),
    ("parachoque_tra", _("Paragolpe trasero")),
    ("guardabarro_di", _("Guardabarro delantero izquierdo")),
    ("guardabarro_dd", _("Guardabarro delantero derecho")),
    ("guardabarro_ti", _("Guardabarro trasero izquierdo")),
    ("guardabarro_td", _("Guardabarro trasero derecho")),
    ("espejo_i", _("Espejo izquierdo")),
    ("espejo_d", _("Espejo derecho")),
    ("faro_di", _("Faro delantero izquierdo")),
    ("faro_dd", _("Faro delantero derecho")),
    ("faro_ti", _("Faro trasero izquierdo")),
    ("faro_td", _("Faro trasero derecho")),
    ("parrilla", _("Parrilla / Rejilla delantera")),
    ("vidrio_del", _("Parabrisas delantero")),
    ("vidrio_tra", _("Luneta trasera")),
    ("llanta_di", _("Llanta delantera izquierda")),
    ("llanta_dd", _("Llanta delantera derecha")),
    ("llanta_ti", _("Llanta trasera izquierda")),
    ("llanta_td", _("Llanta trasera derecha")),
    ("interior", _("Interior")),
    ("otro", _("Otro")),
]

TIPOS_DANO = [
    ("golpe", _("Golpe / abolladura")),
    ("rayon", _("Rayón")),
    ("faltante", _("Faltante / pieza ausente")),
    ("rotura", _("Rotura / rajadura")),
    ("mancha", _("Mancha / suciedad severa")),
    ("corrosion", _("Corrosión / óxido")),
    ("otro", _("Otro")),
]

NIVEL_COMBUSTIBLE = [
    ("vacio", _("Vacío")),
    ("cuarto", _("1/4")),
    ("medio", _("1/2")),
    ("tres_cuartos", _("3/4")),
    ("lleno", _("Lleno")),
]

ESTADO_INSPECCION = [
    ("pendiente", _("Pendiente")),
    ("completada", _("Completada")),
    ("firmada", _("Firmada por cliente")),
]


class InspeccionIngreso(AuditMixin, models.Model):
    empresa = models.ForeignKey(
        "taller.Empresa",
        on_delete=models.CASCADE,
        related_name="inspecciones_ingreso",
        db_index=True,
    )
    documento = models.OneToOneField(
        "taller.Documento",
        on_delete=models.CASCADE,
        related_name="inspeccion_ingreso",
        null=True,
        blank=True,
        db_index=True,
    )
    # null=True agregado en Fase 6.3a: a diferencia de Documento.vehiculo (ya
    # era nullable), este campo era obligatorio -- sin esto, vehiculo_desarme
    # de abajo es inutilizable (el INSERT revienta con NOT NULL constraint
    # apenas el origen es un VehiculoDesarme). on_delete=PROTECT sin cambios:
    # no altera el comportamiento de borrado, solo permite vacío.
    vehiculo = models.ForeignKey(
        "taller.Vehiculo",
        on_delete=models.PROTECT,
        related_name="inspecciones_ingreso",
        null=True,
        blank=True,
        db_index=True,
    )
    # Camino nuevo en paralelo a 'vehiculo' (mismo patrón que 0142 para
    # PiezaDesarme/SugerenciaPiezaDesarme/etc.). Se usa cuando el origen es un
    # VehiculoDesarme creado directo (sin Vehiculo legacy detrás) -- ver
    # taller/desarme/views.py:_guardar_danos_carroceria.
    vehiculo_desarme = models.ForeignKey(
        "taller.VehiculoDesarme",
        on_delete=models.PROTECT,
        related_name="inspecciones_ingreso",
        null=True,
        blank=True,
        db_index=True,
    )
    fecha_hora = models.DateTimeField(auto_now_add=True, db_index=True)
    kilometraje_ingreso = models.PositiveIntegerField(null=True, blank=True)
    nivel_combustible = models.CharField(
        max_length=14,
        choices=NIVEL_COMBUSTIBLE,
        default="medio",
    )
    realizada_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inspecciones_realizadas",
    )
    observaciones_generales = models.TextField(blank=True, default="")
    firma_cliente = models.BooleanField(default=False)
    estado_inspeccion = models.CharField(
        max_length=12,
        choices=ESTADO_INSPECCION,
        default="pendiente",
        db_index=True,
    )

    class Meta:
        verbose_name = _("Inspección de Ingreso")
        verbose_name_plural = _("Inspecciones de Ingreso")
        ordering = ["-fecha_hora"]

    def __str__(self):
        doc_ref = f" – {self.documento.numero_documento}" if self.documento_id else ""
        return f"Inspección #{self.pk}{doc_ref} – {self.vehiculo}"


class DanoInspeccion(models.Model):
    inspeccion = models.ForeignKey(
        InspeccionIngreso,
        on_delete=models.CASCADE,
        related_name="danos",
    )
    zona = models.CharField(max_length=20, choices=ZONAS_VEHICULO)
    tipo_dano = models.CharField(max_length=12, choices=TIPOS_DANO)
    descripcion = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        verbose_name = _("Daño registrado")
        verbose_name_plural = _("Daños registrados")

    def __str__(self):
        return f"{self.get_zona_display()} – {self.get_tipo_dano_display()}"


class EvidenciaInspeccion(models.Model):
    TIPO_CHOICES = [
        ("FOTO", _("Foto")),
        ("VIDEO", _("Video")),
    ]

    inspeccion = models.ForeignKey(
        InspeccionIngreso,
        on_delete=models.CASCADE,
        related_name="evidencias",
    )
    tipo = models.CharField(max_length=5, choices=TIPO_CHOICES, default="FOTO")
    archivo = models.FileField(upload_to="inspecciones_ingreso/%Y/%m/")
    descripcion = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Evidencia de Inspección")
        verbose_name_plural = _("Evidencias de Inspección")
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.get_tipo_display()} – Inspección #{self.inspeccion_id}"
