from datetime import timedelta
from decimal import Decimal
from math import ceil

import pytz

from django.contrib.auth.models import User
from django.db import models
from django.db.models import CheckConstraint, Q
from django.utils import timezone

# Si usas Django ≥4, evita pytz y usa zoneinfo:
# from zoneinfo import ZoneInfo
# from django.utils.timezone import localtime  # recomendado


class Empresa(models.Model):
    PLAN_CHOICES = [
        ("trial", "Prueba Gratuita"),
        ("basic", "Plan Básico"),
        ("premium", "Plan Premium"),
        ("enterprise", "Plan Empresarial"),
    ]

    PAIS_CHOICES = [("CL", "Chile"), ("US", "United States")]
    MONEDA_CHOICES = [("CLP", "CLP"), ("USD", "USD")]

    TIMEZONE_CHOICES = [
        ("America/New_York", "Eastern Time (ET)"),
        ("America/Chicago", "Central Time (CT)"),
        ("America/Denver", "Mountain Time (MT)"),
        ("America/Los_Angeles", "Pacific Time (PT)"),
        ("America/Anchorage", "Alaska Time (AT)"),
        ("Pacific/Honolulu", "Hawaii Time (HT)"),
        ("America/Phoenix", "Arizona Time (MST)"),
        ("America/Santiago", "Chile Time (CLT)"),
    ]

    # Whitelists por país (evita pisar configuraciones válidas del usuario)
    US_TZS = {
        "America/New_York",
        "America/Chicago",
        "America/Denver",
        "America/Los_Angeles",
        "America/Anchorage",
        "Pacific/Honolulu",
        "America/Phoenix",
    }
    CL_TZS = {"America/Santiago"}

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="empresa")
    nombre_taller = models.CharField(max_length=100, default="Mi Taller")
    empresa = models.CharField(
        max_length=100, blank=True, help_text="Razón social o compañía"
    )

    pais = models.CharField(
        max_length=2,
        choices=PAIS_CHOICES,
        default="CL",
        help_text="Define catálogos, moneda y regionalización",
    )

    logo = models.ImageField(upload_to="logos_talleres/", null=True, blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(max_length=100, blank=True, help_text="Email de contacto")

    zona_horaria = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default="America/New_York",
        help_text="Zona horaria del taller",
    )

    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="trial")
    dias_prueba = models.PositiveIntegerField(default=30)
    suscripcion_activa = models.BooleanField(default=True)

    ultimo_pago = models.DateTimeField(null=True, blank=True)
    valor_mensual = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    moneda = models.CharField(max_length=3, choices=MONEDA_CHOICES, default="CLP")

    notificacion_5_dias = models.BooleanField(default=False)
    notificacion_1_dia = models.BooleanField(default=False)
    notificacion_vencido = models.BooleanField(default=False)
    # Opcional: timestamps de notificación
    # notificado_5_dias_en = models.DateTimeField(null=True, blank=True)
    # notificado_1_dia_en = models.DateTimeField(null=True, blank=True)
    # notificado_vencido_en = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.nombre_taller

    def save(self, *args, **kwargs):
        # Set de fecha_fin solo al crear si viene vacía
        if not self.pk and not self.fecha_fin:
            self.fecha_fin = self.fecha_inicio + timedelta(days=self.dias_prueba)

        # Asignación de moneda por país (no pisa manual)
        if self.pais == "US" and self.moneda != "USD":
            self.moneda = "USD"
        elif self.pais == "CL" and self.moneda != "CLP":
            self.moneda = "CLP"

        # Normaliza zona horaria solo si es inválida para el país o está vacía
        if self.pais == "US":
            if not self.zona_horaria or self.zona_horaria not in self.US_TZS:
                self.zona_horaria = "America/New_York"
        else:  # CL
            if not self.zona_horaria or self.zona_horaria not in self.CL_TZS:
                self.zona_horaria = "America/Santiago"

        super().save(*args, **kwargs)

    @property
    def es_usa(self):
        return self.pais == "US"

    @property
    def es_chile(self):
        return self.pais == "CL"

    @property
    def simbolo_moneda(self):
        # Para UI local: "$"; para documentos externos, usa self.moneda para prefijo
        return "$"

    @property
    def formato_moneda(self):
        return {
            "simbolo": self.simbolo_moneda,
            "codigo": self.moneda,
            "decimales": 2 if self.es_usa else 0,
        }

    @property
    def fecha_expiracion(self):
        return self.fecha_fin or (self.fecha_inicio + timedelta(days=self.dias_prueba))

    @property
    def dias_restantes(self):
        now = timezone.now()
        if self.fecha_expiracion <= now:
            return 0
        # ceil de días con mínimo 0
        delta = self.fecha_expiracion - now
        return max(0, ceil(delta.total_seconds() / 86400))

    @property
    def debe_bloquear(self):
        return (timezone.now() > self.fecha_expiracion) and (
            not self.suscripcion_activa
        )

    @property
    def estado_suscripcion(self):
        if self.debe_bloquear:
            return "vencida"
        dias = self.dias_restantes
        if dias <= 1:
            return "critico"
        if dias <= 5:
            return "advertencia"
        return "activa"

    @property
    def color_estado(self):
        return {
            "activa": "green",
            "advertencia": "orange",
            "critico": "red",
            "vencida": "gray",
        }.get(self.estado_suscripcion, "gray")

    def extender_suscripcion(self, dias=30):
        base = (
            self.fecha_fin
            if self.fecha_fin and self.fecha_fin > timezone.now()
            else timezone.now()
        )
        self.fecha_fin = base + timedelta(days=dias)
        self.suscripcion_activa = True
        self.ultimo_pago = timezone.now()
        self.notificacion_5_dias = False
        self.notificacion_1_dia = False
        self.notificacion_vencido = False
        self.save()

    def marcar_pago_recibido(self, monto=None, plan=None):
        if monto is not None:
            self.valor_mensual = Decimal(str(monto))
        if plan:
            self.plan = plan
        self.extender_suscripcion(30)

    # TZ helpers (versión Django-friendly)
    def _tz(self):
        # return ZoneInfo(self.zona_horaria)  # si usas zoneinfo
        return pytz.timezone(self.zona_horaria)  # usando pytz importado directamente

    def convert_to_local_time(self, dt):
        if dt is None:
            return None
        # return localtime(dt, self._tz())  # recomendado
        # Manteniendo tu enfoque con pytz:
        if dt.tzinfo is None:
            dt = timezone.make_aware(dt, timezone.utc)
        return dt.astimezone(self._tz())

    def format_local_datetime(self, dt, format_type="full"):
        local_dt = self.convert_to_local_time(dt)
        if not local_dt:
            return ""
        if format_type == "full":
            return local_dt.strftime("%m/%d/%Y – %I:%M %p")
        if format_type == "date":
            return local_dt.strftime("%m/%d/%Y")
        if format_type == "time":
            return local_dt.strftime("%I:%M %p")
        if format_type == "short":
            return local_dt.strftime("%m/%d – %I:%M %p")
        return local_dt.strftime("%m/%d/%Y – %I:%M %p")

    def now_local(self):
        return self.convert_to_local_time(timezone.now())

    @property
    def timezone_display(self):
        return dict(self.TIMEZONE_CHOICES).get(self.zona_horaria, self.zona_horaria)

    def debe_mostrar_alerta(self):
        return (self.dias_restantes <= 5) and (not self.debe_bloquear)

    def get_mensaje_alerta(self):
        dias = self.dias_restantes
        if dias <= 0:
            return (
                "Tu suscripción ha vencido. Renueva para continuar usando el sistema."
            )
        if dias == 1:
            return "⚠️ Tu suscripción vence mañana. ¡Renueva ahora!"
        if dias <= 5:
            return f"⚠️ Tu suscripción vence en {dias} días. Considera renovar pronto."
        return ""

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        constraints = [
            CheckConstraint(
                check=Q(dias_prueba__gte=0), name="empresa_dias_prueba_gte_0"
            ),
            CheckConstraint(
                check=Q(valor_mensual__gte=0), name="empresa_valor_mensual_gte_0"
            ),
        ]
