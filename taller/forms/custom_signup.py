import logging
import time

from allauth.account.forms import SignupForm
from django import forms

from taller.config.country_settings import CountrySettings
from taller.services.registration_service import RegistrationService
from taller.services.registro_embudo_service import registrar_signup
from taller.utils.country_config import get_country_config

logger = logging.getLogger(__name__)


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
    # ✅ CAMPOS OPCIONALES: first_name, last_name, telefono ahora son opcionales
    first_name = forms.CharField(
        max_length=100,
        label="Nombre",
        required=False,  # ✅ Opcional
        widget=forms.TextInput(
            attrs={"class": "input-futurista", "placeholder": "Nombre (opcional)"}
        ),
        help_text="Ingresa tu nombre (opcional)",
    )
    last_name = forms.CharField(
        max_length=100,
        label="Apellido",
        required=False,  # ✅ Opcional
        widget=forms.TextInput(
            attrs={"class": "input-futurista", "placeholder": "Apellido (opcional)"}
        ),
        help_text="Ingresa tu apellido (opcional)",
    )
    telefono = forms.CharField(
        max_length=20,
        label="Celular (WhatsApp)",
        required=True,  # ✅ OBLIGATORIO - necesario para WhatsApp
        widget=forms.TextInput(
            attrs={"class": "input-futurista", "placeholder": "+56 9 1234 5678", "type": "tel"}
        ),
        help_text="Número de celular con código de país (formato E.164)",
    )
    nombre_taller = forms.CharField(
        max_length=100,
        label="Nombre de tu Taller (Opcional)",
        required=False,  # ✅ FLUJO "LITE": Campo opcional
        widget=forms.TextInput(
            attrs={"class": "input-futurista", "placeholder": "Ej: Taller San Miguel (Opcional)"}
        ),
        help_text="Puedes dejarlo en blanco y configurarlo después en Settings",
    )
    # País: en rutas /us/, /cl/, /br/ → fijo desde URL (no editable).
    # En rutas genéricas → selector visible para elegir país.
    COUNTRY_CHOICES = [
        ("", "--- Seleccione país / Select country ---"),
        ("US", "United States"),
        ("AR", "Argentina"),
        ("CL", "Chile"),
        ("MX", "México"),
        ("PE", "Perú"),
        ("CO", "Colombia"),
        ("EC", "Ecuador"),
        ("BR", "Brasil"),
        ("VE", "Venezuela"),
        ("UY", "Uruguay"),
    ]
    country = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        label="País / Country",
        required=False,
        widget=forms.Select(attrs={"class": "form-select input-futurista", "id": "id_country"}),
    )

    def __init__(self, *args, **kwargs):
        # Extraer country_code, default_phone_prefix y request
        self.country_code = kwargs.pop("country_code", None)
        self.default_phone_prefix = kwargs.pop("default_phone_prefix", None)
        request = kwargs.pop("request", None)
        if request is None and args and hasattr(args[0], "path"):
            request = args[0]

        super().__init__(*args, **kwargs)

        # BLINDAR PAÍS DESDE URL: si la ruta tiene país (/us/, /cl/, /br/), es la única fuente de verdad
        country_from_url = None
        if request:
            country_from_url = (
                CountrySettings.get_country_from_url(request.path)
                or (request.GET.get("from", "") or "").strip().upper()
            )
            if not country_from_url:
                country_from_url = None
            elif CountrySettings.is_country_valid(country_from_url):
                country_from_url = country_from_url.upper()

        if country_from_url:
            self.country_from_url = country_from_url
            self.country_code = country_from_url
            self.country_locked = True
            config = CountrySettings.get_country_config(country_from_url)
            self.country_display_value = (
                config.get("name_es")
                or config.get("name_en")
                or config.get("name")
                or country_from_url
            )
            if "country" in self.fields:
                self.fields["country"].widget = forms.HiddenInput()
                self.fields["country"].initial = country_from_url
        else:
            self.country_from_url = None
            self.country_locked = False
            self.country_display_value = None
            # Sin ruta país: usar ?from=xx o request.country_code (NO fallback a CL)
            if request and not self.country_code:
                from_param = (request.GET.get("from", "") or "").strip().upper()
                self.country_code = from_param or getattr(request, "country_code", None)
                if self.country_code:
                    self.country_code = self.country_code.upper()

        # Sobrescribir first_name si Allauth lo tiene (asegurar que use nuestro campo personalizado)
        # Nuestro campo first_name ya está definido arriba, así que sobrescribirá el de Allauth

        # Email obligatorio (Allauth ya lo hace, pero por claridad)
        if "email" in self.fields:
            self.fields["email"].required = True
            self.fields["email"].widget.attrs.update(
                {"class": "input-futurista", "placeholder": "email@ejemplo.com"}
            )

        # ✅ CAMPOS OPCIONALES: first_name, last_name, telefono ahora son opcionales
        if "first_name" in self.fields:
            self.fields["first_name"].required = False  # ✅ Opcional
            self.fields["first_name"].widget.attrs.update(
                {"class": "input-futurista", "placeholder": "Nombre (opcional)"}
            )
            # Asegurar que el widget sea visible
            if hasattr(self.fields["first_name"].widget, "input_type"):
                self.fields["first_name"].widget.input_type = "text"

        if "last_name" in self.fields:
            self.fields["last_name"].required = False  # ✅ Opcional
            self.fields["last_name"].widget.attrs.update(
                {"class": "input-futurista", "placeholder": "Apellido (opcional)"}
            )
            # Asegurar que el widget sea visible
            if hasattr(self.fields["last_name"].widget, "input_type"):
                self.fields["last_name"].widget.input_type = "text"

        # ✅ Asegurar que telefono sea OBLIGATORIO
        if "telefono" in self.fields:
            self.fields["telefono"].required = True  # ✅ OBLIGATORIO

        # Configurar nombre_taller como opcional
        if "nombre_taller" in self.fields:
            self.fields["nombre_taller"].required = False
            self.fields["nombre_taller"].widget.attrs.update(
                {"class": "input-futurista", "placeholder": "Ej: Taller San Miguel (Opcional)"}
            )

        # ✅ Username opcional - usar email como username si no se proporciona
        # IMPORTANTE: Allauth requiere username, así que lo generamos automáticamente desde email
        if "username" in self.fields:
            self.fields["username"].required = False
            self.fields["username"].widget = (
                forms.HiddenInput()
            )  # Ocultar username, se generará desde email
        if "password1" in self.fields:
            self.fields["password1"].widget.attrs.update(
                {"class": "input-futurista", "placeholder": "••••••••"}
            )
        if "password2" in self.fields:
            self.fields["password2"].widget.attrs.update(
                {"class": "input-futurista", "placeholder": "••••••••"}
            )

        # Preseleccionar país en el selector (solo cuando no está bloqueado por URL)
        if not self.country_locked and self.country_code and "country" in self.fields:
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
        ✅ Normaliza y valida el número de teléfono a formato E.164 (WhatsApp).

        - Campo OBLIGATORIO
        - Quita espacios, guiones, paréntesis
        - Si NO empieza con "+", asume número local y agrega prefijo del país
        - Valida formato internacional (+<codigo><numero>)
        - Longitud entre 8 y 15 dígitos después del +
        - Resultado: siempre formato E.164 (+<código><número>)

        Ejemplos:
        - CL: "9 1234 5678" → "+56912345678"
        - US: "3055551234" → "+13055551234"
        """
        telefono = self.cleaned_data.get("telefono", "").strip()

        # ✅ Campo OBLIGATORIO
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

    def clean_username(self):
        """
        ✅ Generar username automáticamente desde email si no se proporciona.
        Incluye manejo de colisiones: si el username generado ya existe, agrega sufijo aleatorio.

        Esto es necesario porque Allauth puede requerir username aunque ACCOUNT_AUTHENTICATION_METHOD = "email".
        """
        from django.contrib.auth import get_user_model

        User = get_user_model()
        import random
        import string

        username = (
            self.cleaned_data.get("username", "").strip()
            if self.cleaned_data.get("username")
            else ""
        )

        # Si no se proporciona username, generar desde email
        if not username:
            email = (
                self.cleaned_data.get("email", "").strip() if self.cleaned_data.get("email") else ""
            )
            if email:
                # Usar email como username (Allauth lo soporta cuando ACCOUNT_AUTHENTICATION_METHOD = "email")
                username = email
            else:
                # Si tampoco hay email aún, generar uno temporal (esto no debería pasar)
                username = f"user_{int(time.time())}"

        # ✅ Manejo de colisiones: si el username ya existe, agregar sufijo aleatorio
        original_username = username
        max_attempts = 10
        attempt = 0

        while attempt < max_attempts:
            try:
                # Verificar si el username ya existe (excepto si estamos editando el mismo usuario)
                if not User.objects.filter(username=username).exists():
                    break  # Username disponible, salir del loop

                # Generar sufijo aleatorio (4 caracteres alfanuméricos)
                suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))

                # Intentar con sufijo: si es email, insertar antes del @, si no, al final
                if "@" in original_username:
                    local_part, domain = original_username.split("@", 1)
                    username = f"{local_part}_{suffix}@{domain}"
                else:
                    username = f"{original_username}_{suffix}"

                attempt += 1
            except Exception:
                # Si hay error, usar timestamp como fallback
                username = f"user_{int(time.time())}_{random.randint(1000, 9999)}"
                break

        return username

    def clean(self):
        """
        País según URL o selección del usuario. Sin fallback silencioso a CL.

        - Si country_from_url: usar ese país (única fuente de verdad).
        - Si no: requiere país del formulario; si falta, error claro.
        """
        cleaned_data = super().clean()

        if not cleaned_data:
            return cleaned_data

        country = None

        # En rutas país: la URL es la única fuente de verdad
        if getattr(self, "country_from_url", None):
            country = self.country_from_url
        else:
            # Signup sin ruta país: debe venir del formulario (selector)
            country = (cleaned_data.get("country") or "").strip().upper() or (
                self.initial.get("country") if hasattr(self, "initial") else None
            )
            if country:
                country = str(country).upper().strip()

        if not country:
            logger.warning(
                "[CustomSignupForm] No se pudo determinar país: "
                "sin ruta país, sin ?from= y sin selección en formulario"
            )
            raise forms.ValidationError("Debe seleccionar un país / Please select a country")

        if not CountrySettings.is_country_valid(country):
            logger.warning(f"[CustomSignupForm] País no válido en signup: '{country}'")
            raise forms.ValidationError(
                "País no válido. Seleccione uno de la lista / Invalid country. Please select from the list."
            )

        cleaned_data["country"] = country.upper()
        return cleaned_data

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

        # ✅ Actualizar nombres en User (opcionales, usar valores por defecto si están vacíos)
        user.first_name = (
            data.get("first_name", "").strip() or "Usuario"
        )  # Valor por defecto si está vacío
        user.last_name = data.get("last_name", "").strip() or ""  # Opcional
        user.save()

        # 3. País: viene de clean() (garantizado). Prioridad: URL > formulario. Sin fallback a CL.
        country_code = (data.get("country") or "").strip().upper()
        if not country_code:
            logger.error(
                "[CustomSignupForm] save() llamado sin country en cleaned_data. "
                "No se creará empresa."
            )
            raise ValueError(
                "No se pudo determinar el país. No se creará la empresa. "
                "Por favor, registre desde la ruta correcta (/us/, /cl/, etc.) o seleccione un país."
            )

        # ✅ Obtener configuración del país usando sistema centralizado
        config = get_country_config(country_code)

        # 4. ⚡ USAR REGISTRATION SERVICE (Método Parcial)
        # Esto asegura que la empresa se cree con la moneda/impuestos correctos
        # y que sea consistente con otros flujos de registro
        # Allauth ya creó el usuario, solo necesitamos crear la empresa
        # ✅ FLUJO "LITE": Si el usuario no puso nombre_taller, el servicio lo genera automáticamente
        obtuvo_trial = False
        trial_started_at = None
        trial_ends_at = None

        # ✅ Si el usuario no puso nombre, el servicio creará uno genérico
        nombre_taller_usuario = (
            data.get("nombre_taller", "").strip() if data.get("nombre_taller") else ""
        )

        # ✅ Telefono opcional - usar valor normalizado o vacío
        telefono_usuario = data.get("telefono", "").strip() if data.get("telefono") else ""

        try:
            result = RegistrationService.create_company_for_user(
                user=user,
                company_data={
                    # ✅ Pasar nombre_taller (puede ser vacío, el servicio lo generará)
                    "nombre_taller": nombre_taller_usuario,
                    "pais": country_code,
                    "telefono": telefono_usuario,  # ✅ Ya normalizado por clean_telefono (puede ser vacío)
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
