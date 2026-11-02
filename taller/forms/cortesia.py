# taller/forms/cortesia.py
"""
Formulario para otorgar extensiones de cortesía
"""

from django import forms
from django.contrib.auth.models import User


class CortesiaExtensionForm(forms.Form):
    """
    Formulario para otorgar extensión de cortesía a una suscripción
    """

    DURATION_CHOICES = [
        (1, "1 Mes (30 días)"),
        (6, "6 Meses (180 días)"),
        (12, "12 Meses (1 año - 365 días)"),
    ]

    user_email = forms.EmailField(
        label="Email del Usuario",
        help_text="Ingrese el email del usuario al que se le otorgará la cortesía",
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "usuario@ejemplo.com",
                "required": True,
            }
        ),
    )

    duration_months = forms.ChoiceField(
        label="Duración de la Cortesía",
        choices=DURATION_CHOICES,
        help_text="Seleccione la duración de la extensión de cortesía",
        widget=forms.Select(
            attrs={
                "class": "form-control",
                "required": True,
            }
        ),
    )

    reason = forms.CharField(
        label="Razón de la Cortesía",
        help_text="Describa brevemente la razón por la que se otorga esta cortesía (opcional)",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Ej: Cliente fiel, problema técnico resuelto, promoción especial, etc.",
            }
        ),
    )

    def clean_user_email(self):
        """Validar que el usuario existe"""
        email = self.cleaned_data.get("user_email")
        if email:
            try:
                User.objects.get(email=email)
            except User.DoesNotExist:
                raise forms.ValidationError(
                    f"Usuario con email '{email}' no encontrado. "
                    "Por favor verifique el email e intente nuevamente."
                )
        return email

    def clean_duration_months(self):
        """Validar que la duración sea válida"""
        duration = self.cleaned_data.get("duration_months")
        if duration:
            duration = int(duration)
            if duration not in [1, 6, 12]:
                raise forms.ValidationError("Duración inválida. Debe ser 1, 6 o 12 meses.")
        return duration
