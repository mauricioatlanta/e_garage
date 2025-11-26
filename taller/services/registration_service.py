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

        Args:
            user_data: dict con datos del usuario {
                'email': str,
                'password': str,
                'first_name': str (opcional),
                'last_name': str (opcional),
                'username': str (opcional, default: email),
            }
            company_data: dict con datos de la empresa {
                'nombre_taller': str,
                'telefono': str (opcional),
                'direccion': str (opcional),
            }
            plan_type: Tipo de plan ('trial', 'basic', 'premium', 'enterprise')
            country: Código de país ('CL', 'US', 'MX')
            skip_email_verification: Si True, no requiere verificación de email para acceso
            assign_role: Rol a asignar ('Owner', 'Admin', 'Vendedor', 'Tecnico')
            request: HttpRequest (opcional, para construir URLs absolutas)

        Returns:
            dict: {
                'user': User,
                'empresa': Empresa,
                'suscripcion': Suscripcion,
                'activation_code': str (solo si skip_email_verification=False),
            }

        Raises:
            ValueError: Si el email ya existe o datos inválidos
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
        # Esto permite reutilizar la lógica tanto para registro completo como para Allauth
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

        # ✅ OPCIÓN B: NO generar código de activación por defecto
        # Solo generar si explícitamente se requiere (para casos especiales)
        activation_code = None
        if not skip_email_verification and plan_type == "trial":
            # Opcional: Generar código pero no requerirlo para acceso
            activation_code = RegistrationService._generate_activation_code(user, empresa, request)

        # Enviar email de bienvenida
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
        except Exception as e:
            log.error(
                f"[RegistrationService] Error enviando email de bienvenida: {e}", exc_info=True
            )
            # No fallar el registro por error de email

        return {
            "user": user,
            "empresa": empresa,
            "suscripcion": result.get("suscripcion"),
            "activation_code": activation_code,
            "country_config": country_config,
        }

    @staticmethod
    @transaction.atomic
    def create_company_for_user(
        user, company_data, plan_type="trial", assign_role="Owner", request=None
    ):
        """
        Crea empresa para un usuario existente.

        ⚡ USADO POR ALLAUTH: Allauth ya crea el usuario, este método solo crea la empresa.

        Args:
            user: Instancia de User ya creada (por Allauth u otro sistema)
            company_data: dict con datos de la empresa {
                'nombre_taller': str,
                'telefono': str (opcional),
                'direccion': str (opcional),
                'pais': str (código de país, opcional, default: 'CL'),
            }
            plan_type: Tipo de plan ('trial', 'basic', 'premium', 'enterprise')
            assign_role: Rol a asignar ('Owner', 'Admin', 'Vendedor', 'Tecnico')
            request: HttpRequest (opcional, para construir URLs absolutas)

        Returns:
            dict: {
                'empresa': Empresa,
                'suscripcion': Suscripcion (opcional),
                'country_config': dict,
            }

        Raises:
            ValueError: Si el usuario ya tiene empresa o datos inválidos
        """
        # Verificar que el usuario no tenga empresa
        if hasattr(user, "empresa") and user.empresa:
            raise ValueError(f"El usuario {user.email} ya tiene una empresa asociada")

        # Normalizar código de país
        country_code = (company_data.get("pais") or "CL").upper()

        # ✅ Obtener configuración del país usando sistema centralizado
        country_config = get_country_config(country_code)

        # Crear empresa
        nombre_taller = company_data.get(
            "nombre_taller", f"Taller de {user.get_full_name() or user.username or user.email}"
        )

        empresa = Empresa.objects.create(
            user=user,
            nombre_taller=nombre_taller,
            email=user.email,
            telefono=company_data.get("telefono", ""),
            direccion=company_data.get("direccion", ""),
            pais=country_code,
            moneda=country_config["currency"],  # ✅ Automático según país
            zona_horaria=country_config["timezone"],  # ✅ Automático según país
            plan=plan_type,
            suscripcion_activa=True,
        )
        log.info(
            f"[RegistrationService] Empresa creada para usuario existente: {empresa.nombre_taller} ({country_code})"
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

            suscripcion = Suscripcion.objects.create(
                user=user,
                tipo=plan_type,
                fecha_inicio=fecha_inicio.date(),
                fecha_fin=fecha_fin.date() if fecha_fin else None,
                activa=True,
            )
            log.info(f"[RegistrationService] Suscripción creada: {plan_type}")
        except Exception as e:
            log.warning(f"[RegistrationService] No se pudo crear suscripción: {e}")

        # Asignar rol (Owner por defecto)
        try:
            role_group = Group.objects.get(name=assign_role)
            user.groups.add(role_group)
            log.info(f"[RegistrationService] Rol {assign_role} asignado a {user.username}")
        except Group.DoesNotExist:
            log.warning(
                f"[RegistrationService] Grupo {assign_role} no existe, saltando asignación de rol"
            )

        # Crear TeamMember si existe el modelo (compatibilidad con módulo de equipo)
        try:
            from taller.models.team_member import TeamMember

            TeamMember.objects.get_or_create(
                user=user,
                empresa=empresa,
                defaults={
                    "rol": assign_role,
                    "is_active": True,
                },
            )
            log.info(f"[RegistrationService] TeamMember creado para {user.username}")
        except Exception:
            # Si no existe el modelo TeamMember, continuar sin errores
            pass

        # Configurar idioma según país
        activate(country_config.get("lang", "es"))

        return {
            "empresa": empresa,
            "suscripcion": suscripcion,
            "country_config": country_config,
        }

    @staticmethod
    def _generate_activation_code(user, empresa, request=None):
        """
        Genera código de activación para verificación de email.

        Para trial sin verificación inmediata, el código se guarda pero
        no se requiere para el acceso inicial.
        """
        activation_code = get_random_string(12, allowed_chars="0123456789")

        # Guardar código en un modelo de activación si existe
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
                expira_en=timezone.now() + timedelta(days=7),  # Válido por 7 días
            )
            log.info(f"[RegistrationService] Código de activación generado para {user.email}")
        except Exception as e:
            log.warning(f"[RegistrationService] No se pudo guardar código de activación: {e}")

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
        """
        Envía email de bienvenida al nuevo usuario.

        Args:
            user: Usuario creado
            empresa: Empresa creada
            plan_type: Tipo de plan
            country_code: Código de país ('CL', 'US', 'MX', 'PE', 'CO', 'EC', 'BR', 'VE')
            country_config: Configuración del país (opcional, se obtiene si no se proporciona)
            activation_code: Código de activación (opcional)
            skip_verification: Si True, no incluye código en el email
            request: HttpRequest (opcional)
        """
        # Obtener configuración si no se proporciona
        if not country_config:
            country_config = RegistrationService.get_country_config(country_code)

        # Determinar idioma del email
        language = country_config.get("lang", "es")

        # Construir URL de dashboard
        dashboard_url = None
        if request:
            try:
                # Usar el método del servicio para obtener URL
                dashboard_url = RegistrationService.get_dashboard_url_for_country(
                    empresa.pais, request
                )
            except Exception:
                pass

        # Mensaje según idioma
        if language == "en":
            subject = f"Welcome to eGarage - {empresa.nombre_taller}"
            message = f"""
Hello {user.get_full_name() or user.username},

Welcome to eGarage!

Your account has been created successfully:
- Workshop: {empresa.nombre_taller}
- Email: {user.email}
- Plan: {plan_type}

"""
            if dashboard_url:
                message += f"You can access your dashboard here: {dashboard_url}\n\n"

            if not skip_verification and activation_code:
                message += f"Your activation code: {activation_code}\n"
                message += (
                    "(This code is only needed for critical actions like issuing invoices.)\n\n"
                )

            message += """
Note: Your account is active and you can start using the platform immediately.
If you need to verify your email for critical actions, you can do so later.

Thanks for choosing eGarage!
"""
        else:  # Español
            subject = f"Bienvenido a eGarage - {empresa.nombre_taller}"
            message = f"""
Hola {user.get_full_name() or user.username},

¡Bienvenido a eGarage!

Tu cuenta ha sido creada exitosamente:
- Taller: {empresa.nombre_taller}
- Email: {user.email}
- Plan: {plan_type}

"""
            if dashboard_url:
                message += f"Puedes acceder a tu dashboard aquí: {dashboard_url}\n\n"

            if not skip_verification and activation_code:
                message += f"Tu código de activación: {activation_code}\n"
                message += "(Este código solo es necesario para acciones críticas como emitir facturas.)\n\n"

            message += """
Nota: Tu cuenta está activa y puedes comenzar a usar la plataforma inmediatamente.
Si necesitas verificar tu email para acciones críticas, puedes hacerlo más tarde.

¡Gracias por elegir eGarage!
"""

        # Enviar email
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@egarage.cl")
        send_mail(
            subject,
            message,
            from_email,
            [user.email],
            fail_silently=False,
        )
        log.info(f"[RegistrationService] Email de bienvenida enviado a {user.email}")

    @staticmethod
    def verify_activation_code(email, code):
        """
        Verifica código de activación.

        Args:
            email: Email del usuario
            code: Código de activación

        Returns:
            bool: True si el código es válido
        """
        try:
            from taller.models.trial import TrialRegistro

            registro = TrialRegistro.objects.filter(
                email__iexact=email, codigo=code, expira_en__gte=timezone.now()
            ).first()

            if registro:
                # Marcar como verificado
                if hasattr(registro, "verificado"):
                    registro.verificado = True
                    registro.save()
                log.info(f"[RegistrationService] Código verificado para {email}")
                return True

            return False
        except Exception as e:
            log.error(f"[RegistrationService] Error verificando código: {e}", exc_info=True)
            return False

    @staticmethod
    def get_dashboard_url_for_country(country_code, request=None):
        """
        Genera URL del dashboard según país usando CountrySettings.

        Args:
            country_code: Código de país ('CL', 'US', 'MX', 'PE', 'CO', 'EC', 'BR', 'VE')
            request: HttpRequest (opcional)

        Returns:
            str: URL del dashboard
        """
        # Usar CountrySettings para construir URL
        url = CountrySettings.build_url(country_code, "dashboard/", request=request)

        if not url:
            # Fallback: usar configuración de country_config
            country_config = RegistrationService.get_country_config(country_code)
            prefix = country_config.get("url_prefix", "/cl")
            url = f"{prefix}/dashboard/"

            if request:
                try:
                    url = request.build_absolute_uri(url)
                except Exception:
                    pass

        return url
