from allauth.account.views import SignupView

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.utils.translation import activate

from taller.config.country_settings import CountrySettings
from taller.forms.custom_signup import CustomSignupForm
from taller.utils.country_config import get_country_config


class CustomSignupView(SignupView):
    """
    Vista de registro personalizada con Allauth.

    ✅ REFACTORIZADO: Usa RegistrationService a través de CustomSignupForm.
    - Allauth maneja la creación del usuario (hashing, tokens, email)
    - CustomSignupForm.save() crea la empresa usando RegistrationService
    - Configuración de país automática con CountrySettings
    - Sin hardcoding de URLs
    """

    form_class = CustomSignupForm
    template_name = "account/signup.html"

    def get_form_kwargs(self):
        """Pasa country_code y default_phone_prefix al formulario"""
        kwargs = super().get_form_kwargs()

        # ✅ Detectar país con prioridad: 1) parámetro ?from=xx, 2) URL path, 3) request.country_code, 4) CL por defecto
        from_param = self.request.GET.get("from", "").upper()
        current_country = (
            from_param  # Prioridad 1: parámetro ?from=xx
            or CountrySettings.get_country_from_url(self.request.path)  # Prioridad 2: URL path
            or getattr(self.request, "country_code", None)  # Prioridad 3: request.country_code
            or "CL"  # Prioridad 4: CL por defecto
        )
        current_country = current_country.upper()

        # Obtener configuración del país
        country_config = get_country_config(current_country)
        default_phone_prefix = country_config.get("phone_prefix", "+56")

        # Pasar al formulario
        kwargs["country_code"] = current_country
        kwargs["default_phone_prefix"] = default_phone_prefix

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Account - eGarage"
        context["is_universal_signup"] = True

        # Pasar el país actual al template: prioridad ?from=xx, path, request.country_code, CL
        from_param = self.request.GET.get("from", "").upper()
        current_country = (
            from_param
            or CountrySettings.get_country_from_url(self.request.path)
            or getattr(self.request, "country_code", None)
            or "CL"
        )
        current_country = current_country.upper() if current_country else "CL"
        context["current_country"] = current_country
        context["country_config"] = get_country_config(current_country)

        return context

    def form_valid(self, form):
        """
        Allauth maneja la creación del usuario y el envío de emails.
        El formulario (CustomSignupForm.save()) crea la empresa usando RegistrationService.
        """
        # ✅ Obtener el país: 1) selección del usuario en el formulario, 2) ?from=xx, 3) URL, 4) CL por defecto
        from_param = self.request.GET.get("from", "").upper()
        country_code = (
            (form.cleaned_data.get("country") or "")
            .upper()
            .strip()  # Prioridad 1: selector de país en el form
            or from_param
            or getattr(form, "country_code", None)
            or CountrySettings.get_country_from_url(self.request.path)
            or getattr(self.request, "country_code", None)
            or "CL"
        )
        country_code = (country_code or "CL").upper()

        # ✅ Configurar idioma usando country_config
        country_config = get_country_config(country_code)
        language = country_config.get("lang", "es")

        activate(language)
        self.request.session["django_language"] = language
        self.request.session["country"] = country_config.get("namespace", country_code.lower())

        # Guardar el usuario (Allauth maneja el envío de email si ACCOUNT_EMAIL_VERIFICATION = "mandatory")
        # CustomSignupForm.save() crea la empresa automáticamente
        user = form.save(self.request)

        # Obtener nombre del taller desde la empresa del usuario
        nombre_taller = "tu taller"
        try:
            if hasattr(user, "empresa") and user.empresa:
                nombre_taller = user.empresa.nombre_taller
        except Exception:
            # Si no hay empresa aún, usar un valor por defecto
            pass

        # Si NO se requiere verificación de email, hacer login automático
        # para que el usuario pueda acceder directamente después de revisar el correo
        requires_email_verification = (
            getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "mandatory") == "mandatory"
        )

        if not requires_email_verification:
            # Login automático para acceso inmediato después de revisar correo
            backend = settings.AUTHENTICATION_BACKENDS[0]
            user.backend = backend
            login(self.request, user, backend=backend)

        # ✅ Renderizar directamente la página de registro exitoso (Thank You Page)
        # Esto genera expectativa y confianza antes de mostrar el dashboard vacío
        # y evita el Error 500 al intentar redirigir a URLs que pueden no existir
        return render(
            self.request,
            "taller/registro_exitoso.html",
            {
                "email": user.email,
                "nombre_taller": nombre_taller,
                "country_code": country_code,
                "country_config": country_config,
            },
        )

    def form_invalid(self, form):
        # Mantener el idioma seleccionado en caso de error usando country_config
        country_code = (
            CountrySettings.get_country_from_url(self.request.path)
            or getattr(self.request, "country_code", None)
            or "CL"
        )
        country_config = get_country_config(country_code)
        language = country_config.get("lang", "es")
        activate(language)
        return super().form_invalid(form)
