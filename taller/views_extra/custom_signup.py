from allauth.account.views import SignupView

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect
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

        # Detectar país desde URL
        current_country = (
            CountrySettings.get_country_from_url(self.request.path)
            or getattr(self.request, "country_code", None)
            or "CL"
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

        # Pasar el país actual al template usando country_config
        current_country = (
            CountrySettings.get_country_from_url(self.request.path)
            or getattr(self.request, "country_code", None)
            or "CL"
        )
        current_country = current_country.upper()
        context["current_country"] = current_country
        context["country_config"] = get_country_config(
            current_country
        )  # ✅ Usa sistema centralizado

        return context

    def form_valid(self, form):
        """
        Allauth maneja la creación del usuario y el envío de emails.
        El formulario (CustomSignupForm.save()) crea la empresa usando RegistrationService.
        """
        # Obtener el país desde el formulario o desde la URL
        country_code = (
            getattr(form, "country_code", None)
            or CountrySettings.get_country_from_url(self.request.path)
            or getattr(self.request, "country_code", None)
            or "CL"
        )
        country_code = country_code.upper()

        # ✅ Configurar idioma usando country_config
        country_config = get_country_config(country_code)
        language = country_config.get("lang", "es")

        activate(language)
        self.request.session["django_language"] = language
        self.request.session["country"] = country_config.get("namespace", country_code.lower())

        # Guardar el usuario (Allauth maneja el envío de email si ACCOUNT_EMAIL_VERIFICATION = "mandatory")
        # CustomSignupForm.save() crea la empresa automáticamente
        user = form.save(self.request)

        # Verificar si se requiere verificación de email
        requires_email_verification = (
            getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "mandatory") == "mandatory"
        )

        if requires_email_verification:
            # Redirigir a página de registro exitoso
            # Construir URL de registro exitoso con prefijo de país
            registro_exitoso_url = CountrySettings.build_url(
                country_code, "auth/registro-exitoso/", request=self.request
            )
            # Guardar email en sesión para mostrar en la página de éxito
            self.request.session["registro_email"] = user.email
            return redirect(registro_exitoso_url)
        else:
            # Si NO se requiere verificación, hacer login automático
            backend = settings.AUTHENTICATION_BACKENDS[0]
            user.backend = backend
            login(self.request, user, backend=backend)

            # Construir URL de redirección usando CountrySettings
            namespace = country_config.get("namespace", country_code.lower())
            dashboard_url = CountrySettings.build_url(
                country_code, "dashboard/", request=self.request
            )

            # Mensaje de éxito personalizado según país
            if language == "es":
                messages.success(
                    self.request,
                    f"¡Cuenta creada exitosamente! Bienvenido a eGarage {country_config.get('name_es', country_code)}.",
                )
            else:
                messages.success(
                    self.request,
                    f"Account created successfully! Welcome to eGarage {country_config.get('name_en', country_code)}.",
                )

            # Redirigir al dashboard según país
            return redirect(dashboard_url or f"/{country_code.lower()}/dashboard/")

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
