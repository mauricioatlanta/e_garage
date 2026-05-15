from allauth.account.views import SignupView
from allauth.account.adapter import get_adapter
from allauth.account.models import EmailAddress, EmailConfirmationHMAC

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.translation import activate

from taller.config.country_settings import CountrySettings
from taller.forms.custom_signup import CustomSignupForm
from taller.utils.country_config import get_country_config


def _send_confirmation_compat(request, user, signup=True, email=None):
    """
    Envia confirmacion compatible con versiones antiguas/nuevas de allauth.
    Evita depender de allauth.account.utils.send_email_confirmation.
    """
    target_email = (email or getattr(user, "email", "") or "").strip()
    if not target_email:
        return

    email_address = EmailAddress.objects.filter(user=user, email__iexact=target_email).first()
    if email_address is None:
        email_address = EmailAddress.objects.create(
            user=user,
            email=target_email,
            verified=False,
            primary=True,
        )

    confirmation = EmailConfirmationHMAC(email_address)
    adapter = get_adapter(request)
    adapter.send_confirmation_mail(request, confirmation, signup=signup)


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

    def get_initial(self):
        initial = super().get_initial()
        email = (self.request.GET.get("email", "") or "").strip()
        if email:
            initial["email"] = email
        return initial

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
        _send_confirmation_compat(self.request, user, signup=True)

        # Guardar contexto del signup para pantalla intermedia y reenvío de confirmación.
        country_path = country_code.lower()
        lang_path = "en" if country_code == "US" else "es"
        self.request.session["pending_signup_email"] = user.email
        self.request.session["pending_signup_country"] = country_code
        self.request.session["pending_signup_lang"] = lang_path
        self.request.session.modified = True

        login_url = f"/{country_path}/{lang_path}/accounts/login/"
        signup_url = f"/{country_path}/{lang_path}/accounts/signup/?email={user.email}"
        return render(
            self.request,
            "account/signup_email_pending.html",
            {
                "email": user.email,
                "country_code": country_code,
                "language_code": lang_path,
                "country_config": country_config,
                "login_url": login_url,
                "signup_url": signup_url,
            },
        )

    def form_invalid(self, form):
        loc = getattr(self.request, "eg_us_public_signup_lang", None)
        path = (self.request.path or "").rstrip("/") or "/"
        if loc == "en" or (loc is None and path == "/us/signup"):
            activate("en")
        elif loc == "es" or (loc is None and path == "/us/es/signup"):
            activate("es")
        else:
            country_code = CountrySettings.get_country_from_url(self.request.path) or getattr(
                self.request, "country_code", None
            )
            country_config = get_country_config(country_code) if country_code else {"lang": "es"}
            language = country_config.get("lang", "es")
            activate(language)
        return super().form_invalid(form)
