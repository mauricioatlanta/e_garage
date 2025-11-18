from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class SignupCompleteForm(forms.Form):
    """
    Formulario completo de registro con selección de país y plan
    Para empezar a generar ingresos desde día 1
    """

    # === DATOS PERSONALES ===
    nombre = forms.CharField(
        max_length=50,
        label="Nombre",
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Juan",
                "required": "required",
            }
        ),
    )

    apellido = forms.CharField(
        max_length=50,
        label="Apellido",
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Pérez",
                "required": "required",
            }
        ),
    )

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(
            attrs={
                "class": "form-input",
                "placeholder": "juan@example.com",
                "required": "required",
            }
        ),
    )

    # === DATOS DE LA EMPRESA/TALLER ===
    nombre_taller = forms.CharField(
        max_length=200,
        label="Nombre de la Compañía",
        help_text="Nombre de tu taller, tienda de repuestos, vulcanización, etc.",
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Taller Mecánico Los Ángeles",
                "required": "required",
            }
        ),
    )

    telefono = forms.CharField(
        max_length=20,
        label="Teléfono",
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "+56912345678 o (555) 123-4567",
                "required": "required",
            }
        ),
    )

    # === SELECCIÓN DE PAÍS ===
    pais = forms.ChoiceField(
        choices=[
            ("", "--- Selecciona tu país ---"),
            ("BR", "🇧🇷 Brasil"),
            ("CL", "🇨🇱 Chile"),
            ("CO", "🇨🇴 Colombia"),
            ("EC", "🇪🇨 Ecuador"),
            ("MX", "🇲🇽 México"),
            ("PE", "🇵🇪 Perú"),
            ("US", "🇺🇸 United States"),
            ("VE", "🇻🇪 Venezuela"),
        ],
        label="País",
        required=True,
        widget=forms.Select(
            attrs={
                "class": "form-input",
                "onchange": "updatePlanPrices(this.value)",
                "required": "required",
            }
        ),
    )

    # === SELECCIÓN DE PLAN ===
    plan = forms.ChoiceField(
        choices=[
            ("", "--- Selecciona tu plan ---"),
            ("trial", "🎁 Prueba Gratuita (30 días)"),
            ("mensual", "📅 Plan Mensual"),
            ("semestral", "⭐ Plan Semestral (Recomendado)"),
            ("anual", "💎 Plan Anual (Mejor precio)"),
        ],
        label="Plan de Suscripción",
        required=True,
        widget=forms.Select(
            attrs={
                "class": "form-input",
                "onchange": "highlightPlan(this.value)",
                "required": "required",
            }
        ),
    )

    # === CONTRASEÑA ===
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-input",
                "placeholder": "••••••••",
                "required": "required",
            }
        ),
        min_length=8,
        help_text="Mínimo 8 caracteres",
    )

    password2 = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-input",
                "placeholder": "••••••••",
                "required": "required",
            }
        ),
    )

    # === TÉRMINOS Y CONDICIONES ===
    acepta_terminos = forms.BooleanField(
        label="Acepto los términos y condiciones",
        required=True,
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-checkbox",
            }
        ),
    )

    # === VALIDACIONES ===
    def clean_email(self):
        email = self.cleaned_data.get("email", "").lower().strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError("Ya existe una cuenta con este email. ¿Deseas iniciar sesión?")
        return email

    def clean_telefono(self):
        telefono = self.cleaned_data.get("telefono", "").strip()
        pais = self.cleaned_data.get("pais")

        if not pais:
            return telefono

        # Validación por país
        if pais == "CL":
            # Chile: debe tener 56 + 9 dígitos o empezar con 9
            cleaned = "".join(filter(str.isdigit, telefono))
            if not (cleaned.startswith("56") or cleaned.startswith("9")):
                raise ValidationError("Teléfono chileno debe empezar con +56 o 9")
            if len(cleaned) < 9:
                raise ValidationError("Teléfono chileno debe tener al menos 9 dígitos")

        elif pais == "US":
            # USA: debe tener 10 dígitos
            cleaned = "".join(filter(str.isdigit, telefono))
            if len(cleaned) != 10:
                raise ValidationError("Teléfono USA debe tener 10 dígitos: (555) 123-4567")
        elif pais == "MX":
            cleaned = "".join(filter(str.isdigit, telefono))
            if cleaned.startswith("52") and len(cleaned) == 12:
                cleaned = cleaned[2:]
            if len(cleaned) != 10:
                raise ValidationError("Teléfono México debe tener 10 dígitos (ej: 55 1234 5678)")
        elif pais == "CO":
            # Colombia: debe tener 10 dígitos (celular) o 7 dígitos (fijo)
            cleaned = "".join(filter(str.isdigit, telefono))
            if cleaned.startswith("57") and len(cleaned) == 12:
                cleaned = cleaned[2:]  # Quitar código de país
            if len(cleaned) != 10 and len(cleaned) != 7:
                raise ValidationError(
                    "Teléfono colombiano debe tener 10 dígitos (celular) o 7 dígitos (fijo)"
                )
        elif pais == "EC":
            # Ecuador: debe tener 9 dígitos (celular) o 7 dígitos (fijo)
            cleaned = "".join(filter(str.isdigit, telefono))
            if cleaned.startswith("593") and (len(cleaned) == 12 or len(cleaned) == 10):
                cleaned = cleaned[3:]  # Quitar código de país
            if len(cleaned) != 9 and len(cleaned) != 7:
                raise ValidationError(
                    "Teléfono ecuatoriano debe tener 9 dígitos (celular) o 7 dígitos (fijo)"
                )

        return telefono

    def clean_pais(self):
        pais = self.cleaned_data.get("pais")
        if not pais:
            raise ValidationError("Debes seleccionar un país")
        return pais

    def clean_plan(self):
        plan = self.cleaned_data.get("plan")
        if not plan:
            raise ValidationError("Debes seleccionar un plan de suscripción")
        return plan

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2:
            if password1 != password2:
                raise ValidationError("Las contraseñas no coinciden")

            # Validar fortaleza de contraseña
            if len(password1) < 8:
                raise ValidationError("La contraseña debe tener al menos 8 caracteres")

        return cleaned_data
