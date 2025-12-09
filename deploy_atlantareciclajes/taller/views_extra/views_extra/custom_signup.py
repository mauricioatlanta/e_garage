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

    def get_template_names(self):
        """
        ✅ FASE REGISTRO: Seleccionar template según país e idioma.
        Prioridad: template específico por país > template base
        """
        # Detectar país desde URL o request
        current_country = (
            CountrySettings.get_country_from_url(self.request.path)
            or getattr(self.request, "country_code", None)
            or self.request.GET.get("from", "CL").upper()
            or "CL"
        )
        current_country = current_country.upper()

        # Detectar idioma
        country_config = get_country_config(current_country)
        lang = country_config.get("lang", "es")

        # Construir path del template específico
        template_path = f"{current_country.lower()}/{lang}/account/signup.html"

        # Lista de templates a intentar (prioridad)
        templates = [
            template_path,  # Específico por país/idioma
            "account/signup.html",  # Template base
        ]

        return templates

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create Account - eGarage"
        context["is_universal_signup"] = True

        # Pasar el país actual al template usando country_config
        current_country = (
            CountrySettings.get_country_from_url(self.request.path)
            or getattr(self.request, "country_code", None)
            or self.request.GET.get("from", "CL").upper()
            or "CL"
        )
        current_country = current_country.upper()
        context["current_country"] = current_country
        context["country_config"] = get_country_config(
            current_country
        )  # ✅ Usa sistema centralizado
        context["empresa"] = (
            getattr(self.request.user, "empresa", None)
            if self.request.user.is_authenticated
            else None
        )

        return context

    def form_valid(self, form):
        """
        Allauth maneja la creación del usuario y el envío de emails.
        El formulario (CustomSignupForm.save()) crea la empresa usando RegistrationService.
        """
        # Obtener el país seleccionado
        country_code = form.cleaned_data.get("country", "US")

        # ✅ Configurar idioma usando country_config
        country_config = get_country_config(country_code)
        language = country_config.get("lang", "es")

        activate(language)
        self.request.session["django_language"] = language
        self.request.session["country"] = country_config.get("namespace", country_code.lower())

        # Guardar el usuario (Allauth maneja el envío de email si ACCOUNT_EMAIL_VERIFICATION = "mandatory")
        # CustomSignupForm.save() crea la empresa automáticamente
        user = form.save(self.request)

        # ✅ FASE REGISTRO: Siempre hacer auto-login después del registro (todos inician en trial)
        # No requerir verificación de email para acceso inmediato
        backend = (
            settings.AUTHENTICATION_BACKENDS[0]
            if settings.AUTHENTICATION_BACKENDS
            else "django.contrib.auth.backends.ModelBackend"
        )
        user.backend = backend
        login(self.request, user, backend=backend)

        # Construir URL de redirección usando CountrySettings
        namespace = country_config.get("namespace", country_code.lower())
        dashboard_url = CountrySettings.build_url(country_code, "dashboard/", request=self.request)

        # Mensaje de éxito personalizado según país
        if language == "es":
            messages.success(
                self.request,
                f"¡Cuenta creada exitosamente! Bienvenido a eGarage {country_config.get('name_es', country_code)}. Tu prueba de 30 días ha comenzado.",
            )
        else:
            messages.success(
                self.request,
                f"Account created successfully! Welcome to eGarage {country_config.get('name_en', country_code)}. Your 30-day trial has started.",
            )

        # Redirigir al dashboard según país
        return redirect(dashboard_url or f"/{country_code.lower()}/dashboard/")

    def form_invalid(self, form):
        # Mantener el idioma seleccionado en caso de error usando country_config
        country = self.request.POST.get("country", "US")
        country_config = get_country_config(country)
        language = country_config.get("lang", "es")
        activate(language)
        return super().form_invalid(form)
