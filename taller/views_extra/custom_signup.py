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
        """Pasa request, country_code y default_phone_prefix al formulario"""
        kwargs = super().get_form_kwargs()

        # País: URL tiene prioridad (en /us/, /cl/ → fijo). Sin fallback silencioso a CL.
        from_param = (self.request.GET.get("from", "") or "").strip().upper()
        current_country = (
            CountrySettings.get_country_from_url(self.request.path)
            or from_param
            or getattr(self.request, "country_code", None)
        )
        if current_country:
            current_country = current_country.upper()

        # Obtener configuración del país (para prefijo teléfono; puede ser None si sin ruta país)
        country_config = get_country_config(current_country) if current_country else {}
        default_phone_prefix = country_config.get("phone_prefix", "+56")

        kwargs["request"] = self.request
        kwargs["country_code"] = current_country
        kwargs["default_phone_prefix"] = default_phone_prefix

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Account - eGarage"
        context["is_universal_signup"] = True

        # País para contexto: URL, ?from=, request. Sin fallback a CL.
        from_param = (self.request.GET.get("from", "") or "").strip().upper()
        current_country = (
            CountrySettings.get_country_from_url(self.request.path)
            or from_param
            or getattr(self.request, "country_code", None)
        )
        current_country = current_country.upper() if current_country else None
        context["current_country"] = current_country
        context["country_config"] = get_country_config(current_country) if current_country else {}

        return context

    def form_valid(self, form):
        """
        Allauth maneja la creación del usuario y el envío de emails.
        El formulario (CustomSignupForm.save()) crea la empresa usando RegistrationService.
        """
        # País: viene de form.cleaned_data (garantizado por clean(), sin fallback CL)
        country_code = (form.cleaned_data.get("country") or "").strip().upper()
        if not country_code:
            messages.error(
                self.request,
                "No se pudo determinar el país. Por favor, use la ruta correcta (/us/, /cl/, etc.) o seleccione un país.",
            )
            return self.form_invalid(form)

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
        # Idioma para mostrar errores: URL, request, o español por defecto (solo para UI)
        country_code = CountrySettings.get_country_from_url(self.request.path) or getattr(
            self.request, "country_code", None
        )
        country_config = get_country_config(country_code) if country_code else {"lang": "es"}
        language = country_config.get("lang", "es")
        activate(language)
        return super().form_invalid(form)
