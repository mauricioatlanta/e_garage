import time

from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth import get_user_model

from taller.config.country_settings import CountrySettings
from taller.services.registration_service import RegistrationService
from taller.services.registro_embudo_service import registrar_signup
from taller.utils.country_config import get_country_config
from taller.utils.plan_catalog import normalize_plan_code

# ---------------------------------------------------------------------------
# Grupos simplificados de rubros para el selector de signup.
# CASA_REPUESTOS y DESARMADURIA son grupos separados: son negocios distintos
# con flujos distintos (la desarmaduría requiere vehículos donantes, sesiones
# de despiece e inventario de piezas desmontadas).
#
# Convención de almacenamiento:
#   config.rubro_principal = primer rubro real del grupo principal seleccionado
#   config.rubros = lista COMPLETA de rubros reales, incluyendo rubro_principal
#   Invariante: rubro_principal siempre está en rubros.
#
# El límite de 2 grupos adicionales (máx 3 en total) pertenece ÚNICAMENTE
# al formulario de signup. El modelo y el servicio no imponen ese límite.
# ---------------------------------------------------------------------------
SIGNUP_RUBRO_GROUPS = [
    {
        "key": "TALLER_MECANICO",
        "label": "Taller Mecánico",
        "label_en": "Auto Repair Shop",
        "description": "Autos, motos, camiones — reparación y mantención",
        "description_en": "Cars, motorcycles, trucks — repair and maintenance",
        "icon": "🔧",
        "rubros": ["WORKSHOP", "WORKSHOP_MOTO", "WORKSHOP_HEAVY"],
    },
    {
        "key": "CASA_REPUESTOS",
        "label": "Casa de Repuestos",
        "label_en": "Auto Parts Store",
        "description": "Venta de partes y repuestos automotrices",
        "description_en": "Auto parts and accessories sales",
        "icon": "📦",
        "rubros": ["PARTS"],
    },
    {
        "key": "DESARMADURIA",
        "label": "Desarmaduría / Salvage",
        "label_en": "Salvage Yard / Dismantler",
        "description": "Desarme de vehículos, venta de piezas desmontadas",
        "description_en": "Vehicle dismantling and used parts sales",
        "icon": "🔩",
        "rubros": ["DESARMADURIA"],
    },
    {
        "key": "NEUMATICOS",
        "label": "Neumáticos / Vulcanización",
        "label_en": "Tires / Wheel Shop",
        "description": "Venta e instalación de neumáticos y llantas",
        "description_en": "Tire and wheel sales and installation",
        "icon": "⭕",
        "rubros": ["TIRE"],
    },
    {
        "key": "CARROCERIA_DETAILING",
        "label": "Carrocería / Pintura / Detailing",
        "label_en": "Body Shop / Detailing",
        "description": "Reparación de chapa, pintura, lavado y estética",
        "description_en": "Bodywork, paint, wash and detailing",
        "icon": "🎨",
        "rubros": ["BODYSHOP", "DETAILING"],
    },
    {
        "key": "RECICLAJE",
        "label": "Reciclaje",
        "label_en": "Recycling",
        "description": "Compra y reventa de catalíticos y chatarra electrónica",
        "description_en": "Catalytic converter and e-scrap buying and resale",
        "icon": "♻️",
        "rubros": ["RECYCLING"],
    },
    {
        "key": "ESPECIALISTA",
        "label": "Especialista",
        "label_en": "Specialist",
        "description": "Electricidad, escapes, suspensión, audio u otra especialidad",
        "description_en": "Electrical, exhaust, suspension, audio or other specialty",
        "icon": "⚡",
        "rubros": ["ELECTRIC", "EXHAUST", "SUSPENSION_STEERING", "GLASS_AUDIO", "BRAKES"],
    },
    {
        "key": "OTRO",
        "label": "Otro / Mixto",
        "label_en": "Other / Mixed",
        "description": "Negocio no listado o con múltiples giros",
        "description_en": "Unlisted business or multiple services",
        "icon": "⊞",
        "rubros": ["MIXED"],
    },
]

_GROUP_KEY_TO_RUBROS = {g["key"]: g["rubros"] for g in SIGNUP_RUBRO_GROUPS}
_SIGNUP_GROUP_CHOICES = [(g["key"], g["label"]) for g in SIGNUP_RUBRO_GROUPS]
_VALID_GROUP_KEYS = frozenset(_GROUP_KEY_TO_RUBROS)


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
    # ✅ PAÍS: Selector visible para que el usuario elija su país en todos los signups
    COUNTRY_CHOICES = [("", "--- Seleccione país / Select country ---")] + \
        CountrySettings.get_available_countries_for_choices()
    country = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        label="País / Country",
        required=False,
        widget=forms.Select(attrs={"class": "form-select input-futurista", "id": "id_country"}),
    )

    # Campo principal: actividad dominante del negocio (determina producto, color, nav).
    # Se usa HiddenInput porque el template construye el selector visual con JS.
    rubro_principal_signup = forms.ChoiceField(
        choices=[("", "")] + _SIGNUP_GROUP_CHOICES,
        required=True,
        label="Actividad principal",
        widget=forms.HiddenInput(),
        error_messages={
            "required": "Debes seleccionar la actividad principal de tu negocio.",
            "invalid_choice": "Selección no válida.",
        },
    )

    # Actividades adicionales (opcional, máximo 2 extra).
    # Límite de 2 solo aplica a este formulario; el modelo no impone máximo.
    rubros_adicionales = forms.MultipleChoiceField(
        choices=_SIGNUP_GROUP_CHOICES,
        required=False,
        label="Otras actividades",
        widget=forms.CheckboxSelectMultiple(attrs={"class": "rubro-adicional-cb"}),
        help_text="Opcional — máximo 2 actividades adicionales",
    )

    def __init__(self, *args, **kwargs):
        # Extraer kwargs personalizados ANTES de super()
        request = kwargs.pop("request", None)
        self.request = request
        self.country_code = kwargs.pop("country_code", None)
        self.default_phone_prefix = kwargs.pop("default_phone_prefix", None)
        self.signup_lang = "es"

        super().__init__(*args, **kwargs)

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

        # ✅ DETECTAR PAÍS AUTOMÁTICAMENTE desde request (?from=xx) o URL
        # Si aún no tenemos request, intentar obtenerlo del primer argumento posicional
        if request is None and args and hasattr(args[0], "path"):
            request = args[0]

        if request and not self.country_code:
            # Prioridad: 1) parámetro ?from=xx, 2) URL path, 3) request.country_code, 4) CL por defecto
            from_param = request.GET.get("from", "").upper()
            if from_param:
                self.country_code = from_param
            else:
                self.country_code = (
                    CountrySettings.get_country_from_url(request.path)
                    or getattr(request, "country_code", None)
                    or "CL"
                )
            self.country_code = self.country_code.upper()

        # ✅ Preseleccionar país en el selector (desde ?from=xx o URL)
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

        if request and getattr(request, "eg_us_public_signup_lang", None) == "en":
            self.signup_lang = "en"
            self._apply_us_public_signup_english()
        elif request:
            signup_path = (request.path or "").rstrip("/") or "/"
            if signup_path == "/us/signup":
                self.signup_lang = "en"
                self._apply_us_public_signup_english()

    def _apply_us_public_signup_english(self):
        """Etiquetas en inglés para /us/signup/ (formulario con strings en español por defecto)."""
        if "country" in self.fields:
            self.fields["country"].label = "Country"
            ch = list(self.fields["country"].choices)
            if ch:
                ch[0] = ("", "Select country")
            self.fields["country"].choices = ch
        if "first_name" in self.fields:
            self.fields["first_name"].label = "First name"
            self.fields["first_name"].help_text = "Optional"
            self.fields["first_name"].widget.attrs["placeholder"] = "First name (optional)"
        if "last_name" in self.fields:
            self.fields["last_name"].label = "Last name"
            self.fields["last_name"].help_text = "Optional"
            self.fields["last_name"].widget.attrs["placeholder"] = "Last name (optional)"
        if "telefono" in self.fields:
            self.fields["telefono"].label = "Mobile (WhatsApp)"
            self.fields["telefono"].help_text = "Mobile number with country code (E.164 format)"
        if "nombre_taller" in self.fields:
            self.fields["nombre_taller"].label = "Workshop name (optional)"
            self.fields["nombre_taller"].help_text = (
                "You can leave this blank and set it later in Settings"
            )
            self.fields["nombre_taller"].widget.attrs[
                "placeholder"
            ] = "e.g. Main Street Auto (optional)"
        if "password1" in self.fields:
            self.fields["password1"].label = "Password"
        if "password2" in self.fields:
            self.fields["password2"].label = "Confirm password"
        if "email" in self.fields:
            self.fields["email"].widget.attrs["placeholder"] = "you@example.com"
        if "telefono" in self.fields:
            self.fields["telefono"].widget.attrs["placeholder"] = "+1 555 123 4567"
        if "rubro_principal_signup" in self.fields:
            self.fields["rubro_principal_signup"].label = "Primary business type"
            self.fields["rubro_principal_signup"].error_messages = {
                "required": "Please select your primary business type.",
                "invalid_choice": "Invalid selection.",
            }
        if "rubros_adicionales" in self.fields:
            self.fields["rubros_adicionales"].label = "Other activities (optional)"
            self.fields["rubros_adicionales"].help_text = "Optional — up to 2 additional activities"

    def _duplicate_email_error_message(self):
        if self.signup_lang == "en":
            return (
                "This email address is already registered in eGarage. "
                "Please sign in or use the password recovery option."
            )
        return (
            "Esta dirección de correo ya está registrada en eGarage. "
            "Por favor, inicia sesión o usa la opción de recuperar contraseña."
        )

    def _duplicate_phone_error_message(self):
        if self.signup_lang == "en":
            return "This contact number is already linked to a registered eGarage workshop."
        return "Este número de contacto ya está vinculado a un taller registrado en eGarage."

    def clean_rubro_principal_signup(self):
        group = (self.cleaned_data.get("rubro_principal_signup") or "").strip()
        if not group:
            raise forms.ValidationError(
                "Please select your primary business type."
                if self.signup_lang == "en"
                else "Debes seleccionar la actividad principal de tu negocio."
            )
        if group not in _VALID_GROUP_KEYS:
            raise forms.ValidationError(
                "Invalid selection." if self.signup_lang == "en" else "Selección no válida."
            )
        return group

    def clean_rubros_adicionales(self):
        adicionales = list(self.cleaned_data.get("rubros_adicionales") or [])
        principal = (self.cleaned_data.get("rubro_principal_signup") or "").strip()

        # Si el principal fue enviado como adicional también, silenciosamente ignorarlo
        adicionales = [g for g in adicionales if g != principal]

        # Validar claves
        invalid = [g for g in adicionales if g not in _VALID_GROUP_KEYS]
        if invalid:
            raise forms.ValidationError(
                "Invalid selection." if self.signup_lang == "en" else "Selección no válida."
            )

        # Límite de 2 adicionales — solo aplica al signup, no al modelo
        if len(adicionales) > 2:
            raise forms.ValidationError(
                "You can add up to 2 additional activities."
                if self.signup_lang == "en"
                else "Puedes agregar hasta 2 actividades adicionales."
            )
        return adicionales

    def _build_rubros_list(self) -> list:
        """
        Construye la lista completa de rubros reales para persistir.

        Convenio de almacenamiento:
          - rubro_principal = rubros_list[0]
          - config.rubros = rubros_list completo (incluye rubro_principal)
          - Invariante: rubro_principal in config.rubros

        Orden preservado. Sin duplicados. Sin usar set().
        """
        principal_group = self.cleaned_data.get("rubro_principal_signup") or ""
        adicionales = list(self.cleaned_data.get("rubros_adicionales") or [])

        rubros: list = []

        def _add(r: str) -> None:
            if r not in rubros:
                rubros.append(r)

        # Primero: todos los rubros del grupo principal
        for r in _GROUP_KEY_TO_RUBROS.get(principal_group, []):
            _add(r)

        # Luego: rubros de cada grupo adicional (excluyendo el principal)
        for g in adicionales:
            if g == principal_group:
                continue
            for r in _GROUP_KEY_TO_RUBROS.get(g, []):
                _add(r)

        return rubros

    def clean_email(self):
        raw_email = (self.cleaned_data.get("email") or "").strip().lower()
        if not raw_email:
            return raw_email

        try:
            email = super().clean_email()
        except forms.ValidationError:
            if get_user_model().objects.filter(email__iexact=raw_email).exists():
                raise forms.ValidationError(self._duplicate_email_error_message())
            raise

        if get_user_model().objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(self._duplicate_email_error_message())

        return email

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
        country_code = (
            self.cleaned_data.get("country")
            or self.data.get(self.add_prefix("country"))
            or self.country_code
            or "CL"
        )
        country_code = str(country_code).upper().strip() or "CL"
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

        from taller.models.empresa import Empresa

        if Empresa.objects.filter(telefono=telefono_normalizado).exists():
            raise forms.ValidationError(self._duplicate_phone_error_message())

        return telefono_normalizado

    def clean_username(self):
        """
        ✅ Generar username automáticamente desde email si no se proporciona.
        Incluye manejo de colisiones: si el username generado ya existe, agrega sufijo aleatorio.

        Esto es necesario porque Allauth puede requerir username aunque ACCOUNT_AUTHENTICATION_METHOD = "email".
        """
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
        ✅ GARANTIZAR PAÍS AUTOMÁTICAMENTE (Núcleo del Plan B)

        Esto hace que aunque el template no envíe country, aunque el usuario use VPN,
        aunque falte ?from=xx, SIEMPRE haya país válido.

        IMPORTANTE: Este método se ejecuta DESPUÉS de clean_telefono y otros clean_*,
        por lo que tiene acceso a cleaned_data después de todas las validaciones.
        """
        cleaned_data = super().clean()

        # Si cleaned_data está vacío (formulario inválido), retornar sin modificar
        if not cleaned_data:
            return cleaned_data

        # Detectar país con prioridad:
        # 1) cleaned_data.get("country") (si viene del formulario o HiddenInput)
        # 2) self.country_code (detectado en __init__ desde ?from=xx o URL)
        # 3) self.initial.get("country") (si se estableció inicial)
        # 4) CL por defecto
        country = (
            cleaned_data.get("country")
            or self.country_code
            or (hasattr(self, "initial") and self.initial.get("country"))
            or "CL"
        )

        # Normalizar a mayúsculas y validar que sea un código de país válido
        if country:
            country = str(country).upper().strip()
            # Validar que sea uno de los países soportados
            valid_countries = ["US", "AR", "CL", "MX", "PE", "CO", "EC", "BR", "VE", "UY"]
            if country not in valid_countries:
                # ✅ Manejo robusto: Loggear el error pero no fallar el formulario
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"País desconocido '{country}' en signup, usando fallback 'CL'")
                country = "CL"  # Fallback a CL si no es válido
        else:
            country = "CL"

        # ✅ Asegurar que country esté en cleaned_data (siempre hay un valor válido)
        cleaned_data["country"] = country

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

        # 3. ✅ Detectar país: 1) selección del usuario en el formulario, 2) ?from=xx, 3) URL, 4) CL por defecto
        from_param = request.GET.get("from", "").upper()
        raw = (data.get("country") or "").strip().upper()
        country_code = (
            raw
            if raw
            else None  # Prioridad 1: selector de país en el form
            or from_param
            or self.country_code
            or getattr(request, "country_code", None)
            or CountrySettings.get_country_from_url(request.path)
            or "CL"
        )
        country_code = (country_code or "CL").upper()

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

        # ✅ Plan seleccionado por el usuario. Mantiene entrada legacy, guarda moderno.
        plan_type = (request.POST.get("plan", "") or "trial").strip().lower()
        plan_type = normalize_plan_code(plan_type)
        if plan_type not in ("trial", "entry", "growth", "business"):
            plan_type = "trial"

        # Construir lista completa de rubros (rubro_principal siempre está incluido)
        rubros_list = self._build_rubros_list()

        try:
            result = RegistrationService.create_company_for_user(
                user=user,
                company_data={
                    "nombre_taller": nombre_taller_usuario,
                    "pais": country_code,
                    "telefono": telefono_usuario,
                },
                plan_type=plan_type,
                assign_role="Owner",
                request=request,
                rubros_list=rubros_list or None,
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
