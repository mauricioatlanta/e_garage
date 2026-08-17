from datetime import timedelta
from decimal import Decimal
from math import ceil

import pytz

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db import models
from django.db.models import CheckConstraint, Q
from django.utils import timezone
from django.utils.text import slugify

from taller.utils.plan_catalog import PLAN_BUSINESS, PLAN_ENTRY, PLAN_GROWTH, PLAN_TRIAL
from taller.config.country_settings import CountrySettings

# Si usas Django ≥4, evita pytz y usa zoneinfo:
# from zoneinfo import ZoneInfo
# from django.utils.timezone import localtime  # recomendado


class Empresa(models.Model):
    PLAN_CHOICES = [
        # Nombres canónicos internos
        (PLAN_TRIAL, "Trial"),
        (PLAN_ENTRY, "Entry"),
        (PLAN_GROWTH, "Growth"),
        (PLAN_BUSINESS, "Business"),
        # Nombres de negocio (UI: Express / Taller / Pro)
        ("express", "Express (1 usuario)"),
        ("taller", "Taller (hasta 4 usuarios)"),
        ("pro", "Pro (hasta 10 usuarios)"),
        # Legacy
        ("basic", "Plan Básico"),
        ("premium", "Plan Premium"),
        ("enterprise", "Plan Empresarial"),
    ]

    PAIS_CHOICES = [(code, cfg["name_es"]) for code, cfg in CountrySettings.COUNTRIES.items()]
    MONEDA_CHOICES = [
        (currency, currency)
        for currency in dict.fromkeys(
            cfg["currency"] for cfg in CountrySettings.COUNTRIES.values()
        )
    ]

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
        ("America/Argentina/Buenos_Aires", "Argentina Time (ART)"),
        ("America/Lima", "Peru Time (PET)"),
        ("America/Bogota", "Colombia Time (COT)"),
        ("America/Guayaquil", "Ecuador Time (ECT)"),
        ("America/Sao_Paulo", "Brasilia Time (BRT)"),
        ("America/Caracas", "Venezuela Time (VET)"),
        ("America/Montevideo", "Uruguay Time (UYT)"),
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

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="empresa"
    )
    slug = models.SlugField(
        max_length=80,
        unique=True,
        blank=True,
        db_index=False,
        help_text="Identificador URL de la tienda pública (/tienda/{slug})",
    )
    marcas_permitidas_catalogo = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Marcas visibles en el catálogo público, separadas por coma (ej: Peugeot, Citroen). Vacío = todas.",
    )
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
    region = models.CharField(max_length=100, blank=True)
    comuna = models.CharField(max_length=100, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=32, blank=True)  # Migrado desde TallerInfo
    # Indica si la empresa ya usó la prueba gratuita (migrado desde TallerInfo.ha_usado_prueba)
    ha_usado_prueba = models.BooleanField(default=False)
    email = models.EmailField(max_length=100, blank=True, help_text="Email de contacto")

    # Campos para control de trial de 30 días
    is_trial = models.BooleanField(
        default=False, help_text="Indica si la empresa está actualmente en período de prueba"
    )
    trial_started_at = models.DateTimeField(
        null=True, blank=True, help_text="Fecha y hora en que comenzó el período de prueba"
    )
    trial_ends_at = models.DateTimeField(
        null=True, blank=True, help_text="Fecha y hora en que termina el período de prueba"
    )
    trial_already_used = models.BooleanField(
        default=False,
        help_text="Marca que esta empresa ya utilizó una prueba gratis (por email o teléfono)",
    )

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

    # Campos de control de notificaciones de vencimiento
    # NOTA: notificacion_5_dias se reutiliza para notificaciones tempranas (7 y 3 días antes)
    #       para evitar múltiples campos similares. Es un campo genérico de "aviso temprano"
    notificacion_5_dias = models.BooleanField(
        default=False,
        help_text="Indica si se envió notificación temprana (7 o 3 días antes del vencimiento). Reutilizado para ambos intervalos.",
    )
    notificacion_1_dia = models.BooleanField(
        default=False, help_text="Indica si se envió notificación a 1 día antes del vencimiento."
    )
    notificacion_vencido = models.BooleanField(
        default=False, help_text="Indica si se envió notificación cuando la suscripción ya venció."
    )
    # Opcional: timestamps de notificación (descomentar si se necesita auditoría)
    # notificado_5_dias_en = models.DateTimeField(null=True, blank=True)
    # notificado_1_dia_en = models.DateTimeField(null=True, blank=True)
    # notificado_vencido_en = models.DateTimeField(null=True, blank=True)

    # Campos de onboarding
    onboarding_completado = models.BooleanField(
        default=False, help_text="Indica si el usuario ha completado el proceso de onboarding"
    )
    onboarding_step = models.PositiveIntegerField(
        default=1, help_text="Paso actual del proceso de onboarding (1-5)"
    )
    onboarding_started_at = models.DateTimeField(
        null=True, blank=True, help_text="Fecha y hora en que comenzó el onboarding"
    )
    onboarding_completed_at = models.DateTimeField(
        null=True, blank=True, help_text="Fecha y hora en que se completó el onboarding"
    )

    def __str__(self):
        return self.nombre_taller

    @property
    def nombre(self):
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
            country_cfg = CountrySettings.COUNTRIES.get(self.pais, {})
            canonical_currency = country_cfg.get("currency")
            canonical_tz = country_cfg.get("timezone")
            if canonical_currency and self.moneda == "CLP" and self.pais != "CL":
                self.moneda = canonical_currency
            if canonical_tz and self.zona_horaria in ("", "UTC"):
                self.zona_horaria = canonical_tz

        if not self.slug:
            self._generar_slug_unico()

        super().save(*args, **kwargs)

    def _generar_slug_unico(self):
        base = slugify(self.nombre_taller)[:72] or "taller"
        candidato = base
        sufijo = 2
        qs = Empresa.objects.exclude(pk=self.pk)
        while qs.filter(slug=candidato).exists():
            candidato = f"{base}-{sufijo}"
            sufijo += 1
        self.slug = candidato

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

    def marcar_pago_recibido(self, monto=None, plan=None, enviar_notificacion=True):
        """
        Marcar pago como recibido y extender suscripción por 30 días

        Args:
            monto: Monto del pago (opcional)
            plan: Plan de suscripción (opcional)
            enviar_notificacion: Si True, envía notificación de renovación (Email + WhatsApp)
        """
        if plan:
            from taller.utils.plan_catalog import normalize_plan_code

            plan = normalize_plan_code(plan)

        # Guardar estado anterior para detectar tipo de evento
        plan_anterior = self.plan
        es_nueva_suscripcion = not self.suscripcion_activa or self.plan == "trial"
        es_cambio_plan = (
            self.suscripcion_activa
            and plan is not None
            and plan_anterior != plan
            and plan_anterior != "trial"
        )

        if monto is not None:
            self.valor_mensual = Decimal(str(monto))
        if plan:
            self.plan = plan

        # Extender suscripción (sin notificación aquí, la enviaremos después)
        self.extender_suscripcion(30, enviar_notificacion=False)

        # Enviar notificaciones automáticas si se solicita
        if enviar_notificacion:
            try:
                from taller.utils.notificaciones_suscripcion import (
                    notificar_cambio_plan,
                    notificar_nueva_suscripcion,
                    notificar_renovacion_exitosa,
                )

                monto_notificacion = monto if monto is not None else self.valor_mensual
                plan_notificacion = plan if plan else self.plan

                if es_nueva_suscripcion:
                    # A. NUEVA SUSCRIPCIÓN
                    notificar_nueva_suscripcion(
                        empresa=self,
                        plan=plan_notificacion,
                        monto=monto_notificacion,
                        es_nueva_empresa=es_nueva_suscripcion,
                    )
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.info(f"✅ Notificación de nueva suscripción enviada a {self.user.email}")
                elif es_cambio_plan:
                    # B. CAMBIO DE PLAN
                    notificar_cambio_plan(
                        empresa=self,
                        plan_anterior=plan_anterior,
                        plan_nuevo=plan_notificacion,
                        monto=monto_notificacion,
                        fecha_inicio=self.fecha_inicio,
                    )
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.info(f"✅ Notificación de cambio de plan enviada a {self.user.email}")
                else:
                    # C. RENOVACIÓN EXITOSA
                    notificar_renovacion_exitosa(
                        empresa=self,
                        plan=plan_notificacion,
                        monto=monto_notificacion,
                        dias_renovados=30,
                    )
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.info(
                        f"✅ Notificación de renovación exitosa enviada a {self.user.email}"
                    )
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.error(f"⚠️ Error al enviar notificación en marcar_pago_recibido: {str(e)}")
                # No fallar si la notificación falla

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
            duration_months: Duración en meses. El admin puede usar cualquier entero entre 1 y 60.
            reason: Razón de la cortesía (opcional)
            admin_user: Usuario administrador que ejecuta la acción (opcional)

        Returns:
            dict: Resultado de la operación con detalles

        Raises:
            ValueError: Si el usuario no existe o la duración no es válida
        """
        from django.contrib.auth import get_user_model

        User = get_user_model()
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

        # Validar duración. Es una acción administrativa, no un catálogo público de planes.
        try:
            duration_months = int(duration_months)
        except (TypeError, ValueError):
            raise ValueError("Duración inválida. Debe ser un número entero de meses.")
        if duration_months < 1 or duration_months > 60:
            raise ValueError(
                f"Duración inválida. Debe estar entre 1 y 60 meses. Recibido: {duration_months}"
            )

        # 2. Calcular la extensión
        # Obtener fecha base (actual o fecha_fin si es futura)
        fecha_base = (
            empresa.fecha_fin
            if (empresa.fecha_fin and empresa.fecha_fin > timezone.now())
            else timezone.now()
        )

        # Calcular nueva fecha de expiración
        nueva_fecha_fin = fecha_base + relativedelta(months=duration_months)
        dias_a_anadir = max((nueva_fecha_fin - fecha_base).days, 1)

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

    @property
    def is_trial_active(self):
        """Atajo para saber si la empresa está en el plan de prueba"""
        return self.plan == "trial"

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        constraints = [
            CheckConstraint(check=Q(dias_prueba__gte=0), name="empresa_dias_prueba_gte_0"),
            CheckConstraint(check=Q(valor_mensual__gte=0), name="empresa_valor_mensual_gte_0"),
            models.UniqueConstraint(
                fields=["telefono"],
                condition=~Q(telefono=""),
                name="uq_empresa_telefono_present",
            ),
        ]

    # Campo de control para la política de retención de 6 meses
    fecha_baja = models.DateTimeField(
        null=True, 
        blank=True, 
        help_text="Fecha exacta de cancelación o suspensión para calcular la purga de datos a los 180 días"
    )

    @property
    def activa_y_vigente(self):
        if not self.suscripcion_activa:
            return False
        if self.fecha_fin and timezone.now() > self.fecha_fin:
            return False
        return True
