from allauth.account.forms import SignupForm
from django import forms

from taller.config.country_settings import CountrySettings
from taller.services.registration_service import RegistrationService
from taller.utils.country_config import get_country_config


class CustomSignupForm(SignupForm):
    """
    Formulario de registro personalizado con Allauth.

    ✅ FASE REGISTRO - Campos simplificados:
    - Nombre y apellido (obligatorios)
    - Celular/WhatsApp (obligatorio)
    - Email (opcional)
    - Contraseña y confirmación (obligatorios)
    - País (obligatorio si no está en URL)
    - NO se pide nombre de empresa/taller
    """

    # Campos adicionales que Allauth no tiene por defecto
    first_name = forms.CharField(
        max_length=100,
        label="Nombre y Apellido",
        required=True,
        widget=forms.TextInput(
            attrs={"class": "input-futurista", "placeholder": "Nombre y Apellido"}
        ),
        help_text="Ingresa tu nombre completo",
    )
    last_name = forms.CharField(
        max_length=100,
        label="Apellido",
        required=False,  # Opcional si se usa un solo campo de nombre completo
        widget=forms.TextInput(
            attrs={"class": "input-futurista", "placeholder": "Apellido (opcional)"}
        ),
    )
    telefono = forms.CharField(
        max_length=20,
        label="Celular (WhatsApp)",
        required=True,
        widget=forms.TextInput(
            attrs={"class": "input-futurista", "placeholder": "+56 9 1234 5678", "type": "tel"}
        ),
        help_text="Número de celular con código de país",
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
        required=False,  # Puede ser opcional si se detecta de la URL
        widget=forms.Select(attrs={"class": "input-futurista", "id": "id_country"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Email opcional (recomendado pero no obligatorio)
        self.fields["email"].required = False
        self.fields["email"].widget.attrs.update(
            {"class": "input-futurista", "placeholder": "email@ejemplo.com (opcional)"}
        )
        # Username opcional - usar email o telefono como username si no se proporciona
        if "username" in self.fields:
            self.fields["username"].required = False
            self.fields["username"].widget.attrs.update(
                {"class": "input-futurista", "placeholder": "username (opcional)"}
            )
        if "password1" in self.fields:
            self.fields["password1"].widget.attrs.update(
                {"class": "input-futurista", "placeholder": "Contraseña"}
            )
        if "password2" in self.fields:
            self.fields["password2"].widget.attrs.update(
                {"class": "input-futurista", "placeholder": "Confirmar contraseña"}
            )

        # Detectar país desde la URL si no se proporciona
        request = kwargs.get("request") or (args[0] if args else None)
        if request and not self.initial.get("country"):
            country_from_url = CountrySettings.get_country_from_url(request.path)
            if country_from_url:
                self.initial["country"] = country_from_url

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
        # Si solo se proporciona first_name, usarlo como nombre completo
        full_name = data.get("first_name", "").strip()
        if full_name:
            # Intentar dividir nombre y apellido si viene en un solo campo
            name_parts = full_name.split(maxsplit=1)
            user.first_name = name_parts[0]
            user.last_name = data.get("last_name", "") or (
                name_parts[1] if len(name_parts) > 1 else ""
            )
        else:
            user.first_name = data.get("first_name", "")
            user.last_name = data.get("last_name", "")

        # Si no hay email, usar telefono como identificador alternativo
        if not user.email and data.get("telefono"):
            # Generar un email temporal basado en telefono para compatibilidad con Django
            user.email = f"user_{data.get('telefono', '').replace('+', '').replace(' ', '').replace('-', '')}@egarage.temp"
            user.username = user.email  # Usar email como username

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
        # Crear empresa SIN nombre de taller (se puede agregar después)
        # Todos los registros inician con plan trial de 30 días
        try:
            result = RegistrationService.create_company_for_user(
                user=user,
                company_data={
                    "nombre_taller": "",  # ✅ NO pedir nombre de empresa al registrarse
                    "pais": country_code,
                    "telefono": data.get("telefono", ""),
                },
                plan_type="trial",  # ✅ Todos inician con trial de 30 días
                assign_role="Owner",
                request=request,
            )
        except ValueError as e:
            # Si el usuario ya tiene empresa, no hacer nada
            # Esto puede pasar si se registra dos veces por error
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"[CustomSignupForm] Usuario {user.email or user.username} ya tiene empresa: {e}"
            )

        return user
