from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from taller.config.country_settings import CountrySettings
from taller.services.registration_service import RegistrationService
from taller.utils.country_config import get_country_config

from ..forms.suscripcion import FormularioRegistro
from ..models.empresa import Empresa


@login_required
def suscripcion_bloqueada(request):
    return render(
        request,
        "suscripcion_bloqueada.html",
        {"dias_restantes": 0, "empresa": getattr(request, "empresa", None)},
    )


def _get_dashboard_url(country_code: str) -> str:
    """
    Obtiene la URL del dashboard según el país usando CountrySettings.

    Args:
        country_code: Código de país ('CL', 'US', 'MX')

    Returns:
        str: URL del dashboard (ej: '/cl/', '/us/')
    """
    return CountrySettings.build_url(country_code, "dashboard/", request=None) or "/cl/"


def _normaliza_email(email: str) -> str:
    return (email or "").strip().lower()


def registro(request):
    """
    Vista de registro unificada que usa RegistrationService.

    ✅ MEJORAS IMPLEMENTADAS:
    - Usa RegistrationService (sin duplicación de lógica)
    - Acceso inmediato al dashboard (sin código de 6 dígitos)
    - Transacciones atómicas (sin usuarios huérfanos)
    - URLs dinámicas con CountrySettings
    """
    if request.method == "POST":
        form = FormularioRegistro(request.POST, request=request)
        tipo_registro = request.POST.get("tipo_registro")

        if not form.is_valid():
            return render(request, "saas/suscripcion/registro.html", {"form": form})

        email = _normaliza_email(form.cleaned_data["email"])
        telefono = form.cleaned_data.get("telefono", "")
        nombre_taller = form.cleaned_data["nombre_taller"]
        plan = form.cleaned_data["plan"]
        pais = form.cleaned_data["pais"]
        password = form.cleaned_data["password"]

        # Obtener nombre del usuario (puede venir separado o del nombre_taller)
        nombre_usuario = form.cleaned_data.get(
            "nombre", nombre_taller.split()[0] if nombre_taller else "Usuario"
        )

        try:
            # ⚡ USAR REGISTRATION SERVICE (Lógica Unificada)
            result = RegistrationService.register_new_client(
                user_data={
                    "email": email,
                    "password": password,
                    "first_name": nombre_usuario,
                    "username": email,  # Usar email como username
                },
                company_data={
                    "nombre_taller": nombre_taller,
                    "telefono": telefono,
                },
                plan_type=plan,
                country=pais,
                skip_email_verification=True,  # ✅ Acceso inmediato (sin código)
                assign_role="Owner",
                request=request,
            )

            user = result["user"]
            empresa = result["empresa"]

            # Actualizar empresa con datos adicionales si es necesario
            if tipo_registro == "trial":
                empresa.ha_usado_prueba = True
                empresa.save(update_fields=["ha_usado_prueba"])

            # 🚀 LOGIN AUTOMÁTICO (Magic UX - Sin Código)
            user = authenticate(username=email, password=password)
            if user:
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")

            # 🎯 ACCESO INMEDIATO AL DASHBOARD (Opción B - Sin Código)
            dashboard_url = _get_dashboard_url(pais)

            # Obtener configuración del país para mensaje personalizado
            country_config = get_country_config(pais)
            country_name = country_config.get("name", pais)

            # Mensaje de bienvenida personalizado
            if tipo_registro == "trial":
                messages.success(
                    request,
                    f"¡Bienvenido a eGarage! Tu cuenta de prueba está activa en {country_name}. "
                    f"Puedes comenzar a usar la plataforma inmediatamente.",
                )
            else:
                # Para planes pagados, mostrar instrucciones de pago
                messages.info(
                    request,
                    f"¡Cuenta creada exitosamente en {country_name}! "
                    f"Revisa tu email para las instrucciones de pago.",
                )

            # Redirigir al dashboard según país
            return redirect(dashboard_url)

        except ValueError as e:
            # El servicio maneja validaciones (email duplicado, etc.)
            messages.error(request, str(e))
            return render(request, "saas/suscripcion/registro.html", {"form": form})
        except Exception as e:
            # Error inesperado - el servicio hace rollback automático
            messages.error(
                request,
                f"Error al crear tu cuenta. Por favor, intenta nuevamente. "
                f"Si el problema persiste, contacta a soporte.",
            )
            # Log del error para debugging
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"[Registro] Error inesperado: {e}", exc_info=True)
            return render(request, "saas/suscripcion/registro.html", {"form": form})

            # Para planes pagados, enviar email con instrucciones de pago
            # (Esto se maneja ahora en el RegistrationService)
            # El email de instrucciones de pago se envía automáticamente si es necesario

    # GET
    form = FormularioRegistro(request=request)
    return render(request, "saas/suscripcion/registro.html", {"form": form})


# ⚠️ DEPRECATED: Función de activación con código eliminada
# El registro ahora es directo con login automático (Opción B)
# Esta función se mantiene solo para compatibilidad con URLs legacy
# TODO: Eliminar esta función y las URLs asociadas después de verificar que no se usan


def activar(request):
    """
    ⚠️ DEPRECATED: Esta función ya no se usa.

    El registro ahora es directo con login automático.
    Los usuarios acceden inmediatamente al dashboard sin necesidad de código.

    Si alguien llega aquí, redirigir al registro.
    """
    messages.info(
        request,
        "El sistema de activación con código ha sido reemplazado. "
        "El registro ahora es directo. Si ya tienes cuenta, inicia sesión.",
    )
    return redirect("taller:registro")
