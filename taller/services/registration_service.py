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

        ✅ CONTROL DE TRIAL:
        - Verifica si el email o teléfono ya fueron usados para un trial
        - Si ya se usó, crea la empresa sin trial
        - Si no se usó, otorga trial de 30 días

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
                'obtuvo_trial': bool,
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
        # ✅ FLUJO "LITE": Si no se proporciona nombre_taller o está vacío, generar uno automáticamente
        # Asegúrate de que la lógica de "nombre por defecto" sea sólida para que nunca falle la creación
        nombre_taller_raw = (
            company_data.get("nombre_taller", "").strip()
            if company_data.get("nombre_taller")
            else ""
        )

        if not nombre_taller_raw:
            # Generar nombre genérico basado en el nombre del usuario
            # Prioridad: first_name > username > email
            nombre_taller = f"Taller de {user.first_name or user.username or user.email}"
        else:
            nombre_taller = nombre_taller_raw

        # Obtener email y teléfono normalizado
        email = user.email
        telefono = company_data.get("telefono", "")

        if telefono and Empresa.objects.filter(telefono=telefono).exists():
            raise ValueError(f"Ya existe una empresa registrada con el teléfono {telefono}")

        # ✅ VERIFICAR SI YA SE USÓ TRIAL CON ESTE EMAIL O TELÉFONO
        obtuvo_trial = False
        trial_started_at = None
        trial_ends_at = None

        if plan_type == "trial":
            # Buscar si existe alguna empresa con trial_already_used = True
            # que tenga el mismo email o teléfono
            empresa_con_trial_previo = Empresa.objects.filter(
                Q(email=email) | Q(telefono=telefono), trial_already_used=True
            ).first()

            if empresa_con_trial_previo:
                # Ya se usó trial con este email o teléfono
                log.info(
                    f"[RegistrationService] Email {email} o teléfono {telefono} ya usó trial. "
                    f"No se otorga nuevo trial."
                )
                obtuvo_trial = False
                trial_already_used = True
            else:
                # Otorgar trial de 30 días
                obtuvo_trial = True
                trial_started_at = timezone.now()
                trial_ends_at = trial_started_at + timedelta(days=30)
                trial_already_used = True
                log.info(f"[RegistrationService] Otorgando trial de 30 días a {email}")
        else:
            # No es trial, pero marcar como usado si ya se usó antes
            empresa_con_trial_previo = Empresa.objects.filter(
                Q(email=email) | Q(telefono=telefono), trial_already_used=True
            ).first()
            trial_already_used = bool(empresa_con_trial_previo)

        empresa = Empresa.objects.create(
            user=user,
            nombre_taller=nombre_taller,
            email=user.email,
            telefono=telefono,
            direccion=company_data.get("direccion", ""),
            pais=country_code,
            moneda=country_config["currency"],  # ✅ Automático según país
            zona_horaria=country_config["timezone"],  # ✅ Automático según país
            plan=plan_type,
            suscripcion_activa=True,
            # Campos de trial
            # is_trial=obtuvo_trial,  # ✅ DEBE SEGUIR COMENTADO (evita errores de migración)
            trial_started_at=trial_started_at,
            trial_ends_at=trial_ends_at,
            trial_already_used=(
                trial_already_used if plan_type == "trial" else (trial_already_used or False)
            ),
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

        # ✅ REGISTRAR CREACIÓN DE EMPRESA EN EL EMBUDO
        try:
            from taller.services.registro_embudo_service import registrar_empresa_creada

            registrar_empresa_creada(user)
        except Exception as e:
            log.warning(f"[RegistrationService] Error registrando empresa creada en embudo: {e}")

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
        Envía un email de bienvenida profesional con credenciales y próximos pasos.
        """
        if not country_config:
            country_config = get_country_config(country_code)

        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "contacto@egarage.cl")
        login_url = "https://www.egarage.cl/accounts/login/"

        subject = f"🚀 ¡Bienvenido a eGarage! - El centro de operaciones de {empresa.nombre_taller}"

        message = f"""
¡Hola {user.first_name or user.username}!

¡Felicidades! Estás a solo segundos de transformar la gestión de tu taller con eGarage, el mejor centro de operaciones del mundo.

Tu cuenta ha sido configurada con éxito para {empresa.nombre_taller}. Aquí tienes tus credenciales de acceso:

📍 Acceso al Panel: {login_url}
📧 Usuario: {user.email}
🔑 Contraseña: La que elegiste al registrarte

Tu plan actual: {plan_type.upper()} (30 días de prueba gratuita)

¿Qué puedes hacer ahora mismo?
1. Configurar los datos de tu taller (Logo, dirección y contacto).
2. Crear tu primer servicio técnico para un cliente.
3. Emitir órdenes de trabajo digitales para impresionar a tus clientes.

Si tienes dudas, nuestro equipo de soporte está listo para ayudarte.

Atentamente,
El Equipo de eGarage
www.egarage.cl
"""
        try:
            send_mail(subject, message, from_email, [user.email], fail_silently=False)
            log.info(f"[RegistrationService] Email profesional enviado a {user.email}")
        except Exception as e:
            log.error(f"[RegistrationService] Error enviando email: {e}")

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
