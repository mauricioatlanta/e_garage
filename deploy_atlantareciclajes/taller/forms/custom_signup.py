from allauth.account.forms import SignupForm
from django import forms

from taller.config.country_settings import CountrySettings
from taller.services.registration_service import RegistrationService


class CustomSignupForm(SignupForm):
    """
    Formulario de registro personalizado con Allauth.

    ✅ MEJORAS IMPLEMENTADAS:
    - Hereda de SignupForm de Allauth (no UserCreationForm)
    - Campos adicionales: first_name, last_name, nombre_taller, country
    - Usa RegistrationService.create_company_for_user() para crear empresa
    - Integración con CountrySettings para configuración automática
    """

    # Campos adicionales que Allauth no tiene por defecto
    first_name = forms.CharField(
        max_length=30,
        label="Nombre",
        required=True,
        widget=forms.TextInput(attrs={"class": "input-futurista", "placeholder": "Nombre"}),
    )
    last_name = forms.CharField(
        max_length=30,
        label="Apellido",
        required=True,
        widget=forms.TextInput(attrs={"class": "input-futurista", "placeholder": "Apellido"}),
    )
    nombre_taller = forms.CharField(
        max_length=100,
        label="Nombre del Taller",
        required=True,
        widget=forms.TextInput(attrs={"class": "input-futurista", "placeholder": "Mi Taller"}),
    )
    country = forms.ChoiceField(
        choices=[
            ("US", "United States"),
            ("CL", "Chile"),
            ("MX", "México"),
            ("PE", "Perú"),
            ("CO", "Colombia"),
            ("EC", "Ecuador"),
            ("BR", "Brasil"),
            ("VE", "Venezuela"),
        ],
        label="País / Country",
        required=True,
        initial="US",
        widget=forms.Select(attrs={"class": "input-futurista", "id": "id_country"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer email requerido (Allauth ya lo hace, pero por claridad)
        self.fields["email"].widget.attrs.update(
            {"class": "input-futurista", "placeholder": "your@email.com"}
        )
        # Username opcional - usar email como username si no se proporciona
        if "username" in self.fields:
            self.fields["username"].required = False
            self.fields["username"].widget.attrs.update(
                {"class": "input-futurista", "placeholder": "username (opcional)"}
            )
        if "password1" in self.fields:
            self.fields["password1"].widget.attrs.update(
                {"class": "input-futurista", "placeholder": "••••••••"}
            )
        if "password2" in self.fields:
            self.fields["password2"].widget.attrs.update(
                {"class": "input-futurista", "placeholder": "••••••••"}
            )

    def save(self, request):
        """
        Guarda el usuario y crea la empresa usando RegistrationService.

        ⚡ ALLAUTH FLOW:
        1. Allauth crea el usuario (User) con su propio sistema de hashing
        2. Llamamos a RegistrationService.create_company_for_user() para crear empresa
        3. Esto garantiza consistencia con otros flujos de registro
        """
        # 1. Dejar que Allauth cree el usuario (User)
        # Allauth maneja el hashing de contraseña, tokens de email, etc.
        user = super(CustomSignupForm, self).save(request)

        # 2. Recoger datos limpios
        data = self.cleaned_data

        # Actualizar nombres en User (Allauth a veces no lo hace solo)
        user.first_name = data.get("first_name", "")
        user.last_name = data.get("last_name", "")
        user.save()

        # 3. Detectar país (Prioridad: Formulario > Middleware > URL > Default)
        country_code = (
            data.get("country")
            or getattr(request, "country_code", None)
            or CountrySettings.get_country_from_url(request.path)
            or "CL"
        )
        country_code = country_code.upper()

        # ✅ Obtener configuración del país usando sistema centralizado
        config = get_country_config(country_code)

        # 4. ⚡ USAR REGISTRATION SERVICE (Método Parcial)
        # Esto asegura que la empresa se cree con la moneda/impuestos correctos
        # y que sea consistente con otros flujos de registro
        # Allauth ya creó el usuario, solo necesitamos crear la empresa
        try:
            result = RegistrationService.create_company_for_user(
                user=user,
                company_data={
                    "nombre_taller": data.get(
                        "nombre_taller", f"Taller de {user.get_full_name() or user.username}"
                    ),
                    "pais": country_code,
                    "telefono": data.get("telefono", ""),
                },
                plan_type="trial",  # Allauth suele ser registro trial/gratuito
                assign_role="Owner",
                request=request,
            )
        except ValueError as e:
            # Si el usuario ya tiene empresa, no hacer nada
            # Esto puede pasar si se registra dos veces por error
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"[CustomSignupForm] Usuario {user.email} ya tiene empresa: {e}")

        return user
