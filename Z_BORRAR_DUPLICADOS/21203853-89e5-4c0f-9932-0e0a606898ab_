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
        MX = "MX", "México"

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
        moneda_esperada = {
            self.Pais.US: "USD",
            self.Pais.CL: "CLP",
            self.Pais.MX: "MXN",
        }.get(self.pais, "CLP")
        if self.moneda != moneda_esperada:
            # Normalizamos en vez de bloquear
            self.moneda = moneda_esperada

    # --- Helpers de presentación / negocio ---
    def precio_formateado(self) -> str:
        if self.pais == self.Pais.US:
            return f"${self.precio:,.2f} USD"
        if self.pais == self.Pais.MX:
            return f"${self.precio:,.2f} MXN"
        return f"${self.precio:,.0f} CLP"

    def caracteristicas_list(self, lang="en"):
        """Copywriting optimizado por plan - todos tienen mismas funciones reales"""
        if lang == "en":
            if self.tipo_plan == "mensual":
                return [
                    "Unlimited work orders & invoices",
                    "Complete inventory management",
                    "Customer database & history",
                    "AI-powered diagnostics",
                    "Real-time analytics dashboard",
                    "Priority email support",
                ]
            elif self.tipo_plan == "semestral":
                return [
                    "Everything in Monthly, plus:",
                    "Advanced predictive analytics",
                    "Enhanced AI diagnostic reports",
                    "Performance tracking & KPIs",
                    "Automated customer reminders",
                    "Quarterly business reviews",
                ]
            else:  # anual
                return [
                    "Everything in Semi-Annual, plus:",
                    "VIP dedicated account manager",
                    "Custom API integrations",
                    "Advanced multi-location management",
                    "Exclusive early access to new features",
                    "Free migration & onboarding assistance",
                ]
        else:  # español
            if self.tipo_plan == "mensual":
                return [
                    "Órdenes de trabajo ilimitadas",
                    "Gestión completa de inventario",
                    "Base de datos de clientes",
                    "Diagnósticos con IA avanzada",
                    "Dashboard de analíticas en tiempo real",
                    "Soporte prioritario por email",
                ]
            elif self.tipo_plan == "semestral":
                return [
                    "Todo del plan Mensual, más:",
                    "Analíticas predictivas avanzadas",
                    "Reportes IA mejorados",
                    "Seguimiento de rendimiento y KPIs",
                    "Recordatorios automáticos a clientes",
                    "Revisiones de negocio trimestrales",
                ]
            else:  # anual
                return [
                    "Todo del plan Semestral, más:",
                    "Gerente de cuenta VIP dedicado",
                    "Integraciones API personalizadas",
                    "Gestión avanzada multi-sucursal",
                    "Acceso anticipado a nuevas funciones",
                    "Migración y capacitación gratuita",
                ]

    # Accesos directos típicos en vistas/templates
    @classmethod
    def get_vigente(cls, pais: str, tipo_plan: str):
        """Devuelve el plan activo actual para un país y tipo (o None)."""
        return cls.objects.vigente(pais, tipo_plan)
