import time

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
    # ✅ CAMPOS OPCIONALES: first_name, last_name, telefono ahora son opcionales
    first_name = forms.CharField(
        max_length=100,
        label="Nombre",
        required=False,  # ✅ Opcional
        widget=forms.TextInput(attrs={"class": "input-futurista", "placeholder": "Nombre (opcional)"}),
        help_text="Ingresa tu nombre (opcional)",
    )
    last_name = forms.CharField(
        max_length=100,
        label="Apellido",
        required=False,  # ✅ Opcional
        widget=forms.TextInput(attrs={"class": "input-futurista", "placeholder": "Apellido (opcional)"}),
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
            attrs={
                "class": "input-futurista",
                "placeholder": "Ej: Taller San Miguel (Opcional)"
            }
        ),
        help_text="Puedes dejarlo en blanco y configurarlo después en Settings",
    )
    # ✅ PAÍS: Selector visible para que el usuario elija su país en todos los signups
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
            self.fields["username"].widget = forms.HiddenInput()  # Ocultar username, se generará desde email
        if "password1" in self.fields:
            self.fields["password1"].widget.attrs.update(
                {"class": "input-futurista", "placeholder": "••••••••"}
            )
        if "password2" in self.fields:
            self.fields["password2"].widget.attrs.update(
                {"class": "input-futurista", "placeholder": "••••••••"}
            )

        # ✅ DETECTAR PAÍS AUTOMÁTICAMENTE desde request (?from=xx) o URL
        # El request puede venir en kwargs o en args[0] si se pasa como primer argumento posicional
        request = None
        if "request" in kwargs:
            request = kwargs["request"]
        elif args and hasattr(args[0], "path"):
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
        
        username = self.cleaned_data.get("username", "").strip() if self.cleaned_data.get("username") else ""
        
        # Si no se proporciona username, generar desde email
        if not username:
            email = self.cleaned_data.get("email", "").strip() if self.cleaned_data.get("email") else ""
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
                suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
                
                # Intentar con sufijo: si es email, insertar antes del @, si no, al final
                if '@' in original_username:
                    local_part, domain = original_username.split('@', 1)
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
            or (hasattr(self, 'initial') and self.initial.get("country"))
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
        user.first_name = data.get("first_name", "").strip() or "Usuario"  # Valor por defecto si está vacío
        user.last_name = data.get("last_name", "").strip() or ""  # Opcional
        user.save()

        # 3. ✅ Detectar país: 1) selección del usuario en el formulario, 2) ?from=xx, 3) URL, 4) CL por defecto
        from_param = request.GET.get("from", "").upper()
        raw = (data.get("country") or "").strip().upper()
        country_code = (
            raw if raw else None  # Prioridad 1: selector de país en el form
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
        nombre_taller_usuario = data.get("nombre_taller", "").strip() if data.get("nombre_taller") else ""
        
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
