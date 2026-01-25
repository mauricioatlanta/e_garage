"""
Servicio Unificado de Registro (Registration Service)

Maneja toda la lógica de registro de usuarios y creación de empresas.
Centraliza la lógica común para evitar duplicación.
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import activate

from taller.models.empresa import Empresa
from taller.models.suscripcion import Suscripcion
from taller.utils.country_config import get_country_config, get_config_from_empresa
from taller.config.country_settings import CountrySettings

log = logging.getLogger(__name__)
User = get_user_model()


class RegistrationService:
    """
    Servicio dedicado para registro de usuarios y creación de empresas.

    Features:
    - Creación de usuario y empresa en transacción atómica
    - Configuración automática de país, idioma y moneda (usa country_config)
    - Creación de suscripción trial automática
    - Envío de emails de bienvenida
    - Asignación de roles por defecto
    - Multi-tenant seguro
    - Soporte para 8 países (CL, US, MX, PE, CO, EC, BR, VE)
    """

    @staticmethod
    def get_country_config(country_code):
        """
        Obtiene configuración de país usando el sistema centralizado.

        Args:
            country_code: Código de país (CL, US, MX, PE, CO, EC, BR, VE)

        Returns:
            dict: Configuración del país o configuración por defecto (CL)
        """
        return get_country_config(country_code)

    @staticmethod
    def normalize_email(email):
        """Normaliza email a lowercase"""
        return (email or "").strip().lower()

    @staticmethod
    @transaction.atomic
    def register_new_client(
        user_data,
        company_data,
        plan_type="trial",
        country="CL",
        skip_email_verification=False,
        assign_role="Owner",
        request=None,
    ):
        """
        Registra un nuevo cliente y crea su empresa.
        """
        # Normalizar email
        email = RegistrationService.normalize_email(user_data.get("email"))
        if not email:
            raise ValueError("Email es obligatorio")

        # Verificar si el usuario ya existe
        existing_user = User.objects.filter(email__iexact=email).first()
        if existing_user:
            # Verificar si ya tiene empresa
            if Empresa.objects.filter(user=existing_user).exists():
                raise ValueError(f"Ya existe una cuenta con el email {email}")
            # Si existe usuario pero no empresa, usarlo
            user = existing_user
        else:
            # Crear nuevo usuario
            username = user_data.get("username") or email
            password = user_data.get("password")

            if not password:
                raise ValueError("Password es obligatorio")

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=user_data.get("first_name", ""),
                last_name=user_data.get("last_name", ""),
                is_active=True,  # Activo por defecto
            )
            log.info(f"[RegistrationService] Usuario creado: {user.username} ({user.email})")

        # Normalizar código de país
        country_code = (country or "CL").upper()

        # Agregar país a company_data para que create_company_for_user lo use
        company_data_with_country = company_data.copy()
        company_data_with_country["pais"] = country_code

        # ⚡ DELEGAR CREACIÓN DE EMPRESA AL MÉTODO PARCIAL
        result = RegistrationService.create_company_for_user(
            user=user,
            company_data=company_data_with_country,
            plan_type=plan_type,
            assign_role=assign_role,
            request=request,
        )

        empresa = result["empresa"]
        country_config = result["country_config"]

        # Configurar idioma según país
        activate(country_config["lang"])

        activation_code = None
        if not skip_email_verification and plan_type == "trial":
            activation_code = RegistrationService._generate_activation_code(user, empresa, request)

        # Enviar email de bienvenida
        email_sent = False
        email_error = None
        try:
            RegistrationService._send_welcome_email(
                user,
                empresa,
                plan_type,
                country_code,
                country_config,
                activation_code=activation_code,
                skip_verification=skip_email_verification,
                request=request,
            )
            email_sent = True
        except Exception as e:
            email_error = str(e)
            log.error(f"[RegistrationService] Error enviando email: {e}")

        return {
            "user": user,
            "empresa": empresa,
            "suscripcion": result.get("suscripcion"),
            "activation_code": activation_code,
            "country_config": country_config,
            "email_sent": email_sent,
            "email_error": email_error,
        }

    @staticmethod
    @transaction.atomic
    def create_company_for_user(
        user, company_data, plan_type="trial", assign_role="Owner", request=None
    ):
        """
        Crea empresa para un usuario existente.
        """
        # Verificar que el usuario no tenga empresa
        if hasattr(user, "empresa") and user.empresa:
            raise ValueError(f"El usuario {user.email} ya tiene una empresa asociada")

        # Normalizar código de país
        country_code = (company_data.get("pais") or "CL").upper()
        country_config = get_country_config(country_code)

        # Crear empresa
        nombre_taller = company_data.get(
            "nombre_taller", f"Taller de {user.get_full_name() or user.username or user.email}"
        )

        email = user.email
        telefono = company_data.get("telefono", "")

        obtuvo_trial = False
        trial_started_at = None
        trial_ends_at = None

        if plan_type == "trial":
            empresa_con_trial_previo = Empresa.objects.filter(
                Q(email=email) | Q(telefono=telefono), trial_already_used=True
            ).first()

            if empresa_con_trial_previo:
                obtuvo_trial = False
                trial_already_used = True
            else:
                obtuvo_trial = True
                trial_started_at = timezone.now()
                trial_ends_at = trial_started_at + timedelta(days=30)
                trial_already_used = True
        else:
            empresa_con_trial_previo = Empresa.objects.filter(
                Q(email=email) | Q(telefono=telefono), trial_already_used=True
            ).first()
            trial_already_used = bool(empresa_con_trial_previo)

        # ⚡ CORRECCIÓN: Se comentó is_trial porque es una property no editable
        empresa = Empresa.objects.create(
            user=user,
            nombre_taller=nombre_taller,
            email=user.email,
            telefono=telefono,
            direccion=company_data.get("direccion", ""),
            pais=country_code,
            moneda=country_config["currency"],
            zona_horaria=country_config["timezone"],
            plan=plan_type,
            suscripcion_activa=True,
            # is_trial=obtuvo_trial,  <-- COMENTADO PARA EVITAR ATTRIBUTEERROR
            trial_started_at=trial_started_at,
            trial_ends_at=trial_ends_at,
            trial_already_used=(
                trial_already_used if plan_type == "trial" else (trial_already_used or False)
            ),
        )

        # Crear suscripción
        suscripcion = None
        try:
            fecha_inicio = timezone.now()
            fecha_fin = None

            if plan_type == "trial":
                dias_trial = getattr(settings, "TRIAL_DAYS", 30)
                fecha_fin = fecha_inicio + timedelta(days=dias_trial)
            elif plan_type in ["basic", "premium", "enterprise", "mensual", "semestral", "anual"]:
                fecha_fin = fecha_inicio + timedelta(days=30)

            suscripcion_activa = (
                empresa.suscripcion_activa if hasattr(empresa, "suscripcion_activa") else True
            )

            suscripcion = Suscripcion.objects.create(
                user=user,
                tipo=plan_type,
                fecha_inicio=fecha_inicio.date(),
                fecha_fin=fecha_fin.date() if fecha_fin else None,
                activa=suscripcion_activa,
            )
        except Exception as e:
            log.warning(f"[RegistrationService] Error suscripción: {e}")

        # Asignar rol
        try:
            role_group = Group.objects.get(name=assign_role)
            user.groups.add(role_group)
        except Group.DoesNotExist:
            pass

        # Crear TeamMember
        try:
            from taller.models.team_member import TeamMember

            TeamMember.objects.get_or_create(
                user=user,
                empresa=empresa,
                defaults={"rol": assign_role, "is_active": True},
            )
        except Exception:
            pass

        activate(country_config.get("lang", "es"))

        # Registro en embudo
        try:
            from taller.reportes.services.registro_embudo_service import registrar_empresa_creada

            registrar_empresa_creada(user)
        except Exception as e:
            log.warning(f"[RegistrationService] Error embudo: {e}")

        return {
            "empresa": empresa,
            "suscripcion": suscripcion,
            "country_config": country_config,
            "obtuvo_trial": obtuvo_trial,
            "trial_started_at": trial_started_at,
            "trial_ends_at": trial_ends_at,
        }

    @staticmethod
    def _generate_activation_code(user, empresa, request=None):
        activation_code = get_random_string(12, allowed_chars="0123456789")
        try:
            from taller.models.trial import TrialRegistro

            TrialRegistro.objects.create(
                nombre=user.get_full_name() or user.username,
                email=user.email,
                codigo=activation_code,
                ip=request.META.get("REMOTE_ADDR") if request else None,
                user_agent=request.headers.get("user-agent", "") if request else "",
                user=user,
                creado_en=timezone.now(),
                expira_en=timezone.now() + timedelta(days=7),
            )
        except Exception:
            pass
        return activation_code

    @staticmethod
    def _send_welcome_email(
        user,
        empresa,
        plan_type,
        country_code,
        country_config=None,
        activation_code=None,
        skip_verification=False,
        request=None,
    ):
        if not country_config:
            country_config = get_country_config(country_code)

        language = country_config.get("lang", "es")
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@egarage.cl")
        subject = f"Bienvenido a eGarage - {empresa.nombre_taller}"
        message = f"Hola {user.first_name}, tu cuenta ha sido creada."

        try:
            send_mail(subject, message, from_email, [user.email], fail_silently=False)
        except Exception:
            pass

    @staticmethod
    def get_dashboard_url_for_country(country_code, request=None):
        url = CountrySettings.build_url(country_code, "dashboard/", request=request)
        if not url:
            country_config = get_country_config(country_code)
            prefix = country_config.get("url_prefix", "/cl")
            url = f"{prefix}/dashboard/"
        return url
