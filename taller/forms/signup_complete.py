from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from taller.utils.plan_catalog import (
    ALL_PLAN_CODES,
    BILLING_ANNUAL,
    BILLING_MONTHLY,
    LEGACY_BILLING_MAPPING,
    LEGACY_PLAN_MAPPING,
    PLAN_TRIAL,
    normalize_billing_cycle,
    normalize_plan_code,
)


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
    # Estos campos son opcionales y se pueden completar después en Settings
    nombre_taller = forms.CharField(
        max_length=200,
        label="Nombre de la Compañía",
        help_text="Nombre de tu taller, tienda de repuestos, vulcanización, etc.",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Taller Mecánico Los Ángeles",
            }
        ),
    )

    telefono = forms.CharField(
        max_length=20,
        label="Teléfono",
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "+56912345678 o (555) 123-4567",
            }
        ),
    )

    # === SELECCIÓN DE PAÍS ===
    # El país se determina automáticamente desde ?from=cl, pero puede ser sobrescrito
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
        required=False,
        widget=forms.Select(
            attrs={
                "class": "form-input",
                "onchange": "updatePlanPrices(this.value)",
            }
        ),
    )

    # === SELECCIÓN DE PLAN ===
    plan = forms.CharField(
        label="Plan de Suscripción",
        required=True,
        widget=forms.Select(
            choices=[
                ("", "--- Selecciona tu plan ---"),
                ("trial", "🎁 Trial (30 días)"),
                ("entry", "Entry"),
                ("growth", "Growth"),
                ("business", "Business"),
            ],
            attrs={
                "class": "form-input",
                "onchange": "highlightPlan(this.value)",
                "required": "required",
            },
        ),
    )

    billing_cycle = forms.ChoiceField(
        choices=[
            (BILLING_MONTHLY, "Mensual"),
            (BILLING_ANNUAL, "Anual"),
        ],
        label="Periodicidad de pago",
        required=False,
        initial=BILLING_MONTHLY,
        widget=forms.Select(attrs={"class": "form-input"}),
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
        # Si no hay teléfono, está bien (es opcional)
        if not telefono:
            return telefono

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
        # El país es opcional - se puede determinar automáticamente desde ?from=cl
        # Si no se proporciona, la vista usará el valor por defecto
        return pais

    def clean_plan(self):
        raw_plan = self.cleaned_data.get("plan")
        if not raw_plan:
            raise ValidationError("Debes seleccionar un plan de suscripción")

        raw_plan = str(raw_plan).strip().lower()
        valid_legacy_values = set(LEGACY_PLAN_MAPPING) | set(LEGACY_BILLING_MAPPING)
        if raw_plan not in ALL_PLAN_CODES and raw_plan not in valid_legacy_values:
            raise ValidationError("El plan seleccionado no es válido")

        plan = normalize_plan_code(raw_plan)
        if plan == PLAN_TRIAL and raw_plan != PLAN_TRIAL:
            raise ValidationError("El plan seleccionado no es válido")

        raw_billing_cycle = self.cleaned_data.get("billing_cycle")
        if raw_plan in LEGACY_BILLING_MAPPING:
            billing_cycle = normalize_billing_cycle(raw_plan)
        else:
            billing_cycle = normalize_billing_cycle(raw_billing_cycle)
        self.cleaned_data["billing_cycle"] = billing_cycle
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
