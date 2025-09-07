from datetime import timedelta
from decimal import Decimal

import pytz

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


# Modelo que representa al suscriptor/empresa dueña de los datos
class Empresa(models.Model):
    PLAN_CHOICES = [
        ("trial", "Prueba Gratuita"),
        ("basic", "Plan Básico"),
        ("premium", "Plan Premium"),
        ("enterprise", "Plan Empresarial"),
    ]

    # 🌎 Países soportados
    PAIS_CHOICES = [
        ("CL", "Chile"),
        ("US", "United States"),
    ]

    # Zonas horarias comunes para USA
    TIMEZONE_CHOICES = [
        ("America/New_York", "Eastern Time (ET)"),
        ("America/Chicago", "Central Time (CT)"),
        ("America/Denver", "Mountain Time (MT)"),
        ("America/Los_Angeles", "Pacific Time (PT)"),
        ("America/Anchorage", "Alaska Time (AT)"),
        ("Pacific/Honolulu", "Hawaii Time (HT)"),
        ("America/Phoenix", "Arizona Time (MST)"),
        ("America/Santiago", "Chile Time (CLT)"),  # Para clientes existentes
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="empresa")
    nombre_taller = models.CharField(max_length=100, default="Mi Taller")
    empresa = models.CharField(
        max_length=100, blank=True, help_text="Nombre de la empresa/compañía"
    )

    # 🌎 País del suscriptor - determina catálogos, moneda e idioma
    pais = models.CharField(
        max_length=2,
        choices=PAIS_CHOICES,
        default="CL",
        help_text="País del suscriptor - determina catálogos de vehículos, moneda y configuraciones regionales",
    )

    logo = models.ImageField(upload_to="logos_talleres/", null=True, blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(
        max_length=100, blank=True, help_text="Email de contacto de la empresa"
    )

    # 🇺🇸 Zona horaria para localización USA
    zona_horaria = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default="America/New_York",
        help_text="Zona horaria del taller para reportes y alertas precisas",
    )

    # Sistema de suscripciones mejorado
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="trial")
    dias_prueba = models.PositiveIntegerField(default=30)
    suscripcion_activa = models.BooleanField(default=True)

    # Campos para gestión de pagos
    ultimo_pago = models.DateTimeField(null=True, blank=True)
    valor_mensual = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    moneda = models.CharField(max_length=3, default="CLP")

    # Control de notificaciones
    notificacion_5_dias = models.BooleanField(default=False)
    notificacion_1_dia = models.BooleanField(default=False)
    notificacion_vencido = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre_taller

    def save(self, *args, **kwargs):
        """Al crear o actualizar una empresa, establecer configuraciones automáticamente"""
        # Para empresas nuevas, establecer fecha_fin
        if not self.pk and not self.fecha_fin:
            self.fecha_fin = self.fecha_inicio + timedelta(days=self.dias_prueba)

        # Actualizar configuración según país (para empresas nuevas y existentes)
        if self.pais == "US":
            self.moneda = "USD"
            # Solo cambiar zona horaria si está en Chile o no está definida
            if not self.zona_horaria or self.zona_horaria == "America/Santiago":
                self.zona_horaria = "America/New_York"
        else:  # Chile por defecto
            self.moneda = "CLP"
            # Solo cambiar zona horaria si está en USA o no está definida
            if (
                not self.zona_horaria
                or "America/New_York" in self.zona_horaria
                or "America/Chicago" in self.zona_horaria
                or "America/Los_Angeles" in self.zona_horaria
            ):
                self.zona_horaria = "America/Santiago"

        super().save(*args, **kwargs)

    @property
    def es_usa(self):
        """Retorna True si la empresa está en Estados Unidos"""
        return self.pais == "US"

    @property
    def es_chile(self):
        """Retorna True si la empresa está en Chile"""
        return self.pais == "CL"

    @property
    def simbolo_moneda(self):
        """Retorna el símbolo de moneda según el país"""
        return "$" if self.pais in ["US", "CL"] else self.moneda

    @property
    def formato_moneda(self):
        """Retorna el formato de moneda para templates"""
        return {
            "simbolo": self.simbolo_moneda,
            "codigo": self.moneda,
            "decimales": 2 if self.pais == "US" else 0,
        }

    @property
    def fecha_expiracion(self):
        """Retorna la fecha de expiración de la suscripción"""
        if self.fecha_fin:
            return self.fecha_fin
        return self.fecha_inicio + timedelta(days=self.dias_prueba)

    @property
    def dias_restantes(self):
        """Calcula los días restantes de suscripción"""
        now = timezone.now()
        if self.fecha_expiracion > now:
            return (self.fecha_expiracion - now).days
        return 0

    @property
    def debe_bloquear(self):
        """Determina si la cuenta debe ser bloqueada"""
        return timezone.now() > self.fecha_expiracion and not self.suscripcion_activa

    @property
    def estado_suscripcion(self):
        """Retorna el estado actual de la suscripción"""
        dias = self.dias_restantes
        if self.debe_bloquear:
            return "vencida"
        elif dias <= 1:
            return "critico"
        elif dias <= 5:
            return "advertencia"
        else:
            return "activa"

    @property
    def color_estado(self):
        """Retorna el color para mostrar el estado"""
        estado = self.estado_suscripcion
        colores = {
            "activa": "green",
            "advertencia": "orange",
            "critico": "red",
            "vencida": "gray",
        }
        return colores.get(estado, "gray")

    def extender_suscripcion(self, dias=30):
        """Extiende la suscripción por X días"""
        if self.fecha_fin:
            # Si ya expiró, extender desde hoy
            if self.fecha_fin < timezone.now():
                self.fecha_fin = timezone.now() + timedelta(days=dias)
            else:
                # Si aún está activa, extender desde la fecha actual de fin
                self.fecha_fin = self.fecha_fin + timedelta(days=dias)
        else:
            self.fecha_fin = timezone.now() + timedelta(days=dias)

        self.suscripcion_activa = True
        self.ultimo_pago = timezone.now()

        # Resetear notificaciones
        self.notificacion_5_dias = False
        self.notificacion_1_dia = False
        self.notificacion_vencido = False

        self.save()

    def marcar_pago_recibido(self, monto=None, plan=None):
        """Marca que se recibió un pago y extiende la suscripción"""
        if monto:
            self.valor_mensual = Decimal(str(monto))
        if plan:
            self.plan = plan

        # Extender suscripción por 30 días
        self.extender_suscripcion(30)

    # 🇺🇸 MÉTODOS PARA MANEJO DE TIMEZONE USA
    def get_timezone_obj(self):
        """Retorna objeto pytz de la zona horaria"""
        return pytz.timezone(self.zona_horaria)

    def convert_to_local_time(self, dt):
        """Convierte datetime UTC a hora local del taller"""
        if dt is None:
            return None

        # Si ya tiene timezone info, convertir a UTC primero
        if dt.tzinfo is not None:
            dt = dt.astimezone(pytz.UTC)
        else:
            # Asumir que es UTC
            dt = pytz.UTC.localize(dt)

        # Convertir a timezone local
        local_tz = self.get_timezone_obj()
        return dt.astimezone(local_tz)

    def format_local_datetime(self, dt, format_type="full"):
        """Formatea datetime en hora local con formato USA"""
        if dt is None:
            return ""

        local_dt = self.convert_to_local_time(dt)
        if local_dt is None:
            return ""

        if format_type == "full":
            # MM/DD/YYYY – hh:mm AM/PM
            return local_dt.strftime("%m/%d/%Y – %I:%M %p")
        elif format_type == "date":
            # MM/DD/YYYY
            return local_dt.strftime("%m/%d/%Y")
        elif format_type == "time":
            # hh:mm AM/PM
            return local_dt.strftime("%I:%M %p")
        elif format_type == "short":
            # MM/DD – hh:mm AM/PM
            return local_dt.strftime("%m/%d – %I:%M %p")
        else:
            return local_dt.strftime("%m/%d/%Y – %I:%M %p")

    def now_local(self):
        """Retorna el datetime actual en la zona horaria local"""
        utc_now = timezone.now()
        return self.convert_to_local_time(utc_now)

    @property
    def timezone_display(self):
        """Nombre legible de la zona horaria"""
        timezone_names = dict(self.TIMEZONE_CHOICES)
        return timezone_names.get(self.zona_horaria, self.zona_horaria)
        print(
            f"✅ Pago procesado para {self.nombre_taller}. Nueva fecha de vencimiento: {self.fecha_fin}"
        )

    def debe_mostrar_alerta(self):
        """Determina si debe mostrar alerta de vencimiento"""
        return self.dias_restantes <= 5 and not self.debe_bloquear

    def get_mensaje_alerta(self):
        """Retorna el mensaje de alerta apropiado"""
        dias = self.dias_restantes
        if dias <= 0:
            return (
                "Tu suscripción ha vencido. Renueva para continuar usando el sistema."
            )
        elif dias == 1:
            return "⚠️ Tu suscripción vence mañana. ¡Renueva ahora!"
        elif dias <= 5:
            return f"⚠️ Tu suscripción vence en {dias} días. Considera renovar pronto."
        return ""

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
