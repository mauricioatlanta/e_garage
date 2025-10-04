from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, UniqueConstraint


class PrecioSuscripcionQuerySet(models.QuerySet):
    def activos(self):
        return self.filter(activo=True)

    def para_pais(self, pais: str):
        return self.filter(pais=pais)

    def vigente(self, pais: str, tipo_plan: str):
        return self.activos().filter(pais=pais, tipo_plan=tipo_plan).first()


class PrecioSuscripcionManager(models.Manager):
    def get_queryset(self):
        return PrecioSuscripcionQuerySet(model=self.model, using=self._db, hints=None)

    # Atajos en el manager
    def activos(self):
        return self.get_queryset().activos()

    def para_pais(self, pais: str):
        return self.get_queryset().para_pais(pais)

    def vigente(self, pais: str, tipo_plan: str):
        return self.get_queryset().vigente(pais, tipo_plan)


class PrecioSuscripcion(models.Model):
    """Precios de suscripción por país (con histórico y plan vigente)."""

    class TipoPlan(models.TextChoices):
        MENSUAL = "mensual", "Mensual"
        SEMESTRAL = "semestral", "Semestral"
        ANUAL = "anual", "Anual"

    class Pais(models.TextChoices):
        CL = "CL", "Chile"
        US = "US", "Estados Unidos"

    tipo_plan = models.CharField(max_length=20, choices=TipoPlan.choices, db_index=True)
    pais = models.CharField(max_length=2, choices=Pais.choices, db_index=True)

    # Precio y moneda (en BD guardamos números, la moneda va atada al país)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    moneda = models.CharField(max_length=3, default="CLP")

    activo = models.BooleanField(default=True, db_index=True)

    # Metadatos del plan
    nombre_plan = models.CharField(max_length=100, default="Plan Estándar")
    descripcion = models.TextField(blank=True)

    # Características incluidas
    documentos_ilimitados = models.BooleanField(default=True)
    usuarios_incluidos = models.PositiveIntegerField(default=5)
    soporte_prioritario = models.BooleanField(default=True)
    reportes_avanzados = models.BooleanField(default=True)
    diagnostico_ia = models.BooleanField(default=True)
    api_incluida = models.BooleanField(default=False)
    multisucursal = models.BooleanField(default=False)

    objects = PrecioSuscripcionManager()

    class Meta:
        verbose_name = "Precio de Suscripción"
        verbose_name_plural = "Precios de Suscripciones"
        ordering = ["pais", "tipo_plan", "-activo"]
        constraints = [
            # Evita duplicados activos por (pais, tipo_plan); permite históricos inactivos
            UniqueConstraint(
                fields=["tipo_plan", "pais"],
                condition=Q(activo=True),
                name="uniq_precio_activo_por_pais_y_plan",
            ),
        ]
        indexes = [
            models.Index(fields=["pais", "tipo_plan"]),
            models.Index(fields=["activo", "pais"]),
        ]

    def __str__(self):
        return f"{self.get_pais_display()} - {self.get_tipo_plan_display()}: {self.precio_formateado()}"

    # --- Validaciones de negocio ---
    def clean(self):
        # Precio no negativo
        if self.precio is None or self.precio < Decimal("0"):
            raise ValidationError("El precio debe ser mayor o igual a 0.")

        # Usuarios incluidos al menos 1
        if self.usuarios_incluidos < 1:
            raise ValidationError("Debe incluir al menos 1 usuario.")

        # Moneda coherente por país
        moneda_esperada = "USD" if self.pais == self.Pais.US else "CLP"
        if self.moneda != moneda_esperada:
            # Normalizamos en vez de bloquear
            self.moneda = moneda_esperada

    # --- Helpers de presentación / negocio ---
    def precio_formateado(self) -> str:
        if self.pais == self.Pais.US:
            return f"${self.precio:,.2f} USD"
        return f"${self.precio:,.0f} CLP"

    def caracteristicas_list(self):
        feats = []
        if self.documentos_ilimitados:
            feats.append("Documentos ilimitados")
        if self.usuarios_incluidos:
            feats.append(f"Hasta {self.usuarios_incluidos} usuarios")
        if self.reportes_avanzados:
            feats.append("Reportes avanzados")
        if self.diagnostico_ia:
            feats.append("Diagnóstico IA incluido")
        if self.soporte_prioritario:
            feats.append("Soporte prioritario")
        if self.api_incluida:
            feats.append("API personalizada")
        if self.multisucursal:
            feats.append("Multi-sucursales")
        return feats

    # Accesos directos típicos en vistas/templates
    @classmethod
    def get_vigente(cls, pais: str, tipo_plan: str):
        """Devuelve el plan activo actual para un país y tipo (o None)."""
        return cls.objects.vigente(pais, tipo_plan)
