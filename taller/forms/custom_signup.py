from allauth.account.forms import SignupForm
from django import forms

from taller.config.country_settings import CountrySettings
from taller.services.registration_service import RegistrationService
from taller.services.registro_embudo_service import registrar_signup
from taller.utils.country_config import get_country_config


class CustomSignupForm(SignupForm):
    """
    Formulario de registro personalizado con Allauth.

    ✅ MEJORAS IMPLEMENTADAS:
    - Hereda de SignupForm de Allauth (no UserCreationForm)
    - Campos adicionales: first_name (Nombre y Apellido), telefono
    - Email obligatorio y único (Allauth)
    - País se detecta automáticamente desde URL (no se pregunta)
    - Validación y normalización de teléfono con prefijo del país
    - Usa RegistrationService.create_company_for_user() para crear empresa
    - Integración con CountrySettings para configuración automática
    """

    # Campos adicionales que Allauth no tiene por defecto
    first_name = forms.CharField(
        max_length=100,
        label="Nombre",
        required=True,
        widget=forms.TextInput(attrs={"class": "input-futurista", "placeholder": "Nombre"}),
        help_text="Ingresa tu nombre",
    )
    last_name = forms.CharField(
        max_length=100,
        label="Apellido",
        required=True,
        widget=forms.TextInput(attrs={"class": "input-futurista", "placeholder": "Apellido"}),
        help_text="Ingresa tu apellido",
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
        required=True,
        widget=forms.Select(attrs={"class": "input-futurista", "id": "id_country"}),
    )

    def __init__(self, *args, **kwargs):
        # Extraer country_code y default_phone_prefix si se pasan
        self.country_code = kwargs.pop("country_code", None)
        self.default_phone_prefix = kwargs.pop("default_phone_prefix", None)

        super().__init__(*args, **kwargs)

        # Sobrescribir first_name si Allauth lo tiene (asegurar que use nuestro campo personalizado)
        # Nuestro campo first_name ya está definido arriba, así que sobrescribirá el de Allauth

        # Email obligatorio (Allauth ya lo hace, pero por claridad)
        if "email" in self.fields:
            self.fields["email"].required = True
            self.fields["email"].widget.attrs.update(
                {"class": "input-futurista", "placeholder": "email@ejemplo.com"}
            )

        # Asegurar que first_name y last_name estén configurados y visibles
        if "first_name" in self.fields:
            self.fields["first_name"].required = True
            self.fields["first_name"].widget.attrs.update(
                {"class": "input-futurista", "placeholder": "Nombre"}
            )
            # Asegurar que el widget sea visible
            if hasattr(self.fields["first_name"].widget, "input_type"):
                self.fields["first_name"].widget.input_type = "text"

        if "last_name" in self.fields:
            self.fields["last_name"].required = True
            self.fields["last_name"].widget.attrs.update(
                {"class": "input-futurista", "placeholder": "Apellido"}
            )
            # Asegurar que el widget sea visible
            if hasattr(self.fields["last_name"].widget, "input_type"):
                self.fields["last_name"].widget.input_type = "text"

        # Asegurar que telefono esté configurado
        if "telefono" in self.fields:
            self.fields["telefono"].required = True

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

        # Detectar país desde request si no se proporcionó
        # El request puede venir en kwargs o en args[0] si se pasa como primer argumento posicional
        request = None
        if "request" in kwargs:
            request = kwargs["request"]
        elif args and hasattr(args[0], "path"):
            request = args[0]

        if request and not self.country_code:
            self.country_code = (
                CountrySettings.get_country_from_url(request.path)
                or getattr(request, "country_code", None)
                or "CL"
            )
            self.country_code = self.country_code.upper()

        # Establecer país inicial en el campo country si se detectó desde URL
        if self.country_code and "country" in self.fields:
            self.fields["country"].initial = self.country_code

        # Obtener configuración del país y prefijo telefónico
        if self.country_code:
            country_config = get_country_config(self.country_code)
            if not self.default_phone_prefix:
                self.default_phone_prefix = country_config.get("phone_prefix", "+56")

            # Ajustar placeholder según país
            if self.country_code == "CL":
                placeholder = "Ej: +56 9 1234 5678"
            elif self.country_code == "US":
                placeholder = "Ej: +1 305 123 4567"
            else:
                placeholder = f"Ej: {self.default_phone_prefix} 9 1234 5678"

            self.fields["telefono"].widget.attrs["placeholder"] = placeholder
            # Opcional: establecer initial con prefijo
            # self.fields["telefono"].initial = self.default_phone_prefix + " "

    def clean_telefono(self):
        """
        Normaliza y valida el número de teléfono.

        - Quita espacios, guiones, paréntesis
        - Si no empieza con "+", asume número local y agrega prefijo
        - Valida formato internacional (+<codigo><numero>)
        - Longitud entre 8 y 15 dígitos después del +
        """
        telefono = self.cleaned_data.get("telefono", "").strip()

        if not telefono:
            raise forms.ValidationError("El teléfono es obligatorio")

        # Normalizar: quitar espacios, guiones, paréntesis
        telefono_normalizado = (
            telefono.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        )

        # Obtener prefijo del país
        country_code = self.country_code or "CL"
        country_config = get_country_config(country_code)
        default_phone_prefix = self.default_phone_prefix or country_config.get(
            "phone_prefix", "+56"
        )

        # Si no empieza con "+", asumir número local y agregar prefijo
        if not telefono_normalizado.startswith("+"):
            # Quitar cualquier + que pueda estar en el medio
            telefono_normalizado = telefono_normalizado.replace("+", "")
            # Agregar prefijo
            telefono_normalizado = default_phone_prefix + telefono_normalizado

        # Validar formato: debe empezar con +
        if not telefono_normalizado.startswith("+"):
            raise forms.ValidationError(
                "El teléfono debe incluir el código de país (ej: +56 9 1234 5678)"
            )

        # Validar que después del + solo haya dígitos
        numero_sin_prefijo = telefono_normalizado[1:]  # Quitar el +
        if not numero_sin_prefijo.isdigit():
            raise forms.ValidationError(
                "El teléfono solo puede contener números y el código de país"
            )

        # Validar longitud (8-15 dígitos después del +)
        if len(numero_sin_prefijo) < 8:
            raise forms.ValidationError("El número de teléfono es demasiado corto")
        if len(numero_sin_prefijo) > 15:
            raise forms.ValidationError("El número de teléfono es demasiado largo")

        return telefono_normalizado

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

        # 3. Detectar país desde formulario, URL o contexto
        country_code = (
            data.get("country")
            or self.country_code
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
        obtuvo_trial = False
        trial_started_at = None
        trial_ends_at = None

        try:
            result = RegistrationService.create_company_for_user(
                user=user,
                company_data={
                    "nombre_taller": f"Taller de {user.get_full_name() or user.username}",
                    "pais": country_code,
                    "telefono": data.get("telefono", ""),  # Ya normalizado por clean_telefono
                },
                plan_type="trial",  # Allauth suele ser registro trial/gratuito
                assign_role="Owner",
                request=request,
            )
            # Obtener información del trial del resultado
            obtuvo_trial = result.get("obtuvo_trial", False)
            trial_started_at = result.get("trial_started_at")
            trial_ends_at = result.get("trial_ends_at")
        except ValueError as e:
            # Si el usuario ya tiene empresa, no hacer nada
            # Esto puede pasar si se registra dos veces por error
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"[CustomSignupForm] Usuario {user.email} ya tiene empresa: {e}")

        # 5. ✅ REGISTRAR EN EL EMBUDO
        registrar_signup(
            user=user,
            pais=country_code,
            obtuvo_trial=obtuvo_trial,
            trial_started_at=trial_started_at,
            trial_ends_at=trial_ends_at,
        )

        return user
