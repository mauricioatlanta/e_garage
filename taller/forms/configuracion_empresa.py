from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import ClearableFileInput

from taller.models import ConfiguracionEmpresa

MAX_LOGO_MB = 5
ALLOWED_IMAGE_MIMES = {"image/png", "image/jpeg", "image/webp", "image/gif"}


class ConfiguracionEmpresaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionEmpresa
        fields = [
            "nombre_publico",
            "tagline",
            "logo",
            "direccion",
            "telefono",
            "email_contacto",
            "sitio_web",
            "moneda",
            "tasa_impuesto",
            "aplicar_impuesto_por_defecto",
            "dividir_por_tecnico",
        ]
        widgets = {"logo": ClearableFileInput(attrs={"accept": "image/*"})}

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")
        if not logo:
            return logo
        if logo.size > MAX_LOGO_MB * 1024 * 1024:
            raise ValidationError(f"El logo no puede exceder {MAX_LOGO_MB}MB.")
        if (
            hasattr(logo, "content_type")
            and logo.content_type not in ALLOWED_IMAGE_MIMES
        ):
            raise ValidationError("Formato de imagen no soportado.")
        return logo
