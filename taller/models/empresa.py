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

    PAIS_CHOICES = [
        ("CL", "Chile"),
        ("US", "United States"),
        ("MX", "México"),
    ]
    MONEDA_CHOICES = [("CLP", "CLP"), ("USD", "USD"), ("MXN", "MXN")]

    TIMEZONE_CHOICES = [
        ("America/New_York", "Eastern Time (ET)"),
        ("America/Chicago", "Central Time (CT)"),
        ("America/Denver", "Mountain Time (MT)"),
        ("America/Los_Angeles", "Pacific Time (PT)"),
        ("America/Anchorage", "Alaska Time (AT)"),
        ("Pacific/Honolulu", "Hawaii Time (HT)"),
        ("America/Phoenix", "Arizona Time (MST)"),
        ("America/Santiago", "Chile Time (CLT)"),
        ("America/Mexico_City", "Central Mexico Time (CST)"),
        ("America/Monterrey", "Norte Mexico Time"),
        ("America/Tijuana", "Pacific Mexico Time"),
        ("America/Cancun", "Quintana Roo Time"),
        ("America/Mazatlan", "Pacific Mexico Time (MX)"),
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
    MX_TZS = {
        "America/Mexico_City",
        "America/Cancun",
        "America/Monterrey",
        "America/Tijuana",
        "America/Mazatlan",
    }

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="empresa")
    nombre_taller = models.CharField(
        max_length=100, default="Mi Taller"
    )  # Migrado desde TallerInfo
    empresa = models.CharField(max_length=100, blank=True, help_text="Razón social o compañía")

    pais = models.CharField(
        max_length=2,
        choices=PAIS_CHOICES,
        default="CL",
        help_text="Define catálogos, moneda y regionalización",
    )

    logo = models.ImageField(upload_to="logos_talleres/", null=True, blank=True)
    direccion = models.CharField(max_length=200, blank=True)
    telefono = models.CharField(max_length=32, blank=True)  # Migrado desde TallerInfo
    # Indica si la empresa ya usó la prueba gratuita (migrado desde TallerInfo.ha_usado_prueba)
    ha_usado_prueba = models.BooleanField(default=False)
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
    valor_mensual = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
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
        elif self.pais == "MX" and self.moneda != "MXN":
            self.moneda = "MXN"

        # Normaliza zona horaria solo si es inválida para el país o está vacía
        if self.pais == "US":
            if not self.zona_horaria or self.zona_horaria not in self.US_TZS:
                self.zona_horaria = "America/New_York"
        elif self.pais == "CL":
            if not self.zona_horaria or self.zona_horaria not in self.CL_TZS:
                self.zona_horaria = "America/Santiago"
        elif self.pais == "MX":
            if not self.zona_horaria or self.zona_horaria not in self.MX_TZS:
                self.zona_horaria = "America/Mexico_City"
        else:
            if not self.zona_horaria:
                self.zona_horaria = "UTC"

        super().save(*args, **kwargs)

    @property
    def es_usa(self):
        return self.pais == "US"

    @property
    def es_chile(self):
        return self.pais == "CL"

    @property
    def es_mexico(self):
        return self.pais == "MX"

    @property
    def simbolo_moneda(self):
        # Para UI local: "$"; para documentos externos, usa self.moneda para prefijo
        return "$"

    @property
    def formato_moneda(self):
        return {
            "simbolo": self.simbolo_moneda,
            "codigo": self.moneda,
            "decimales": 2 if self.pais in ("US", "MX") else 0,
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
        return (timezone.now() > self.fecha_expiracion) and (not self.suscripcion_activa)

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

    def extender_suscripcion(self, dias=30, enviar_notificacion=False):
        """
        Extender suscripción por un número de días

        Args:
            dias: Número de días a extender
            enviar_notificacion: Si True, envía notificación de renovación (Email + WhatsApp)
        """
        base = (
            self.fecha_fin if self.fecha_fin and self.fecha_fin > timezone.now() else timezone.now()
        )
        fecha_fin_anterior = self.fecha_fin
        self.fecha_fin = base + timedelta(days=dias)
        self.suscripcion_activa = True
        self.ultimo_pago = timezone.now()
        self.notificacion_5_dias = False
        self.notificacion_1_dia = False
        self.notificacion_vencido = False
        self.save()

        # Enviar notificación de renovación si se solicita
        # (solo si la suscripción ya estaba activa y se está extendiendo)
        if enviar_notificacion and self.suscripcion_activa and fecha_fin_anterior:
            try:
                from taller.utils.notificaciones_suscripcion import notificar_renovacion_exitosa

                notificar_renovacion_exitosa(
                    empresa=self,
                    plan=self.plan,
                    monto=self.valor_mensual,
                    dias_renovados=dias,
                )
                import logging

                logger = logging.getLogger(__name__)
                logger.info(f"✅ Notificación de renovación enviada a {self.user.email}")
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(f"⚠️ Error al enviar notificación de renovación: {str(e)}")

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
            return "Tu suscripción ha vencido. Renueva para continuar usando el sistema."
        if dias == 1:
            return "⚠️ Tu suscripción vence mañana. ¡Renueva ahora!"
        if dias <= 5:
            return f"⚠️ Tu suscripción vence en {dias} días. Considera renovar pronto."
        return ""

    @classmethod
    def admin_grant_courtesy_extension(
        cls, user_email, duration_months, reason="", admin_user=None
    ):
        """
        Función administrativa para otorgar extensión de cortesía a una suscripción

        Args:
            user_email: Email del usuario al que se le otorga la cortesía
            duration_months: Duración en meses (1, 6 o 12)
            reason: Razón de la cortesía (opcional)
            admin_user: Usuario administrador que ejecuta la acción (opcional)

        Returns:
            dict: Resultado de la operación con detalles

        Raises:
            ValueError: Si el usuario no existe o la duración no es válida
        """
        from django.contrib.auth.models import User
        from taller.models.auditoria import LogAuditoria
        from taller.utils.notificaciones_suscripcion import notificar_renovacion_exitosa

        # 1. Validación de inputs
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            raise ValueError(f"Usuario con email '{user_email}' no encontrado")

        try:
            empresa = cls.objects.get(user=user)
        except cls.DoesNotExist:
            raise ValueError(f"Empresa asociada al usuario '{user_email}' no encontrada")

        # Validar duración
        valid_durations = [1, 6, 12]
        if duration_months not in valid_durations:
            raise ValueError(
                f"Duración inválida. Debe ser 1, 6 o 12 meses. Recibido: {duration_months}"
            )

        # 2. Calcular la extensión
        # Calcular días según meses
        days_map = {
            1: 30,
            6: 180,
            12: 365,
        }
        dias_a_anadir = days_map[duration_months]

        # Obtener fecha base (actual o fecha_fin si es futura)
        fecha_base = (
            empresa.fecha_fin
            if (empresa.fecha_fin and empresa.fecha_fin > timezone.now())
            else timezone.now()
        )

        # Calcular nueva fecha de expiración
        nueva_fecha_fin = fecha_base + timedelta(days=dias_a_anadir)

        # Guardar estado anterior para auditoría
        datos_antes = {
            "fecha_fin": empresa.fecha_fin.isoformat() if empresa.fecha_fin else None,
            "suscripcion_activa": empresa.suscripcion_activa,
            "plan": empresa.plan,
        }

        # 3. Actualizar DB
        empresa.fecha_fin = nueva_fecha_fin
        empresa.suscripcion_activa = True
        empresa.ultimo_pago = timezone.now()
        empresa.notificacion_5_dias = False
        empresa.notificacion_1_dia = False
        empresa.notificacion_vencido = False
        empresa.save()

        # Guardar estado posterior para auditoría
        datos_despues = {
            "fecha_fin": empresa.fecha_fin.isoformat(),
            "suscripcion_activa": empresa.suscripcion_activa,
            "plan": empresa.plan,
        }

        # 4. Crear registro de auditoría
        admin_username = admin_user.username if admin_user else "ADMIN_SYSTEM"
        descripcion = (
            f"Extensión de cortesía otorgada: {duration_months} mes(es) "
            f"({dias_a_anadir} días). Nueva fecha de expiración: {nueva_fecha_fin.strftime('%Y-%m-%d')}. "
            f"Razón: {reason if reason else 'No especificada'}"
        )

        LogAuditoria.log_accion(
            usuario=(
                admin_user if admin_user else user
            ),  # Usar admin_user si existe, sino el usuario de la empresa
            empresa=empresa,
            accion="UPDATE",
            modelo="EMPRESA",
            objeto_id=empresa.id,
            descripcion=descripcion,
            datos_antes=datos_antes,
            datos_despues=datos_despues,
        )

        # 5. Enviar notificación especializada de cortesía
        try:
            notificar_renovacion_exitosa(
                empresa=empresa,
                plan=empresa.plan,
                monto=Decimal("0.00"),  # Monto cero para indicar que es gratuito
                dias_renovados=dias_a_anadir,
                is_courtesy=True,  # Flag de cortesía
                duration_months=duration_months,  # Meses otorgados
            )
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar notificación de cortesía: {str(e)}")
            # No fallar si la notificación falla

        # 6. Enviar notificación de auditoría interna por WhatsApp
        try:
            from django.conf import settings
            from taller.utils.notificaciones_suscripcion import enviar_whatsapp_a_numero

            # Número de administrador para notificaciones de auditoría
            # Puede ser configurado en settings o usar el valor por defecto
            admin_phone = getattr(settings, "ADMIN_AUDIT_PHONE", "+56963607348")

            # Obtener los detalles de la extensión
            duration_display = f"{duration_months} {'Meses' if duration_months > 1 else 'Mes'}"

            # Crear el mensaje de auditoría interna
            mensaje_auditoria = (
                f"🚨 AUDITORÍA - CORTESÍA APROBADA\n"
                f"✅ Extensión de plan ejecutada por Admin.\n"
                f"👤 USUARIO: {user_email}\n"
                f"🎁 DURACIÓN: {duration_display}\n"
                f"📜 RAZÓN: {reason if reason else 'No especificada'}\n"
                f"📅 NUEVA FECHA FIN: {empresa.fecha_fin.strftime('%d/%m/%Y')}"
            )

            # Enviar WhatsApp de auditoría (usar empresa para obtener configuración si está disponible)
            enviar_whatsapp_a_numero(
                numero_telefono=admin_phone,
                mensaje=mensaje_auditoria,
                empresa=empresa,  # Pasar empresa para intentar usar su configuración
            )

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error al enviar notificación de auditoría interna: {str(e)}")
            # No fallar si la notificación de auditoría falla

        return {
            "success": True,
            "empresa": empresa.nombre_taller,
            "user_email": user_email,
            "duration_months": duration_months,
            "dias_anadidos": dias_a_anadir,
            "fecha_anterior": fecha_base.strftime("%Y-%m-%d"),
            "nueva_fecha_fin": nueva_fecha_fin.strftime("%Y-%m-%d"),
            "reason": reason,
            "admin": admin_username,
        }

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        constraints = [
            CheckConstraint(check=Q(dias_prueba__gte=0), name="empresa_dias_prueba_gte_0"),
            CheckConstraint(check=Q(valor_mensual__gte=0), name="empresa_valor_mensual_gte_0"),
        ]
