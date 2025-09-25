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

    def __init__(self, *args, **kwargs):
        # Extraer request de kwargs antes de llamar a super()
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        # Detectar el país basado en la URL o contexto
        if request:
            # Si la URL contiene /us/, es USA
            if "/us/" in request.path:
                # Para USA, solo mostrar USD
                self.fields["moneda"].widget = forms.Select(
                    choices=[("USD", "USD - Dólares Americanos")]
                )
                self.fields["moneda"].initial = "USD"
                # Para USA, tasa de impuesto por defecto 0.00 (sin sales tax)
                if not self.instance.pk:  # Solo si es nueva configuración
                    self.fields["tasa_impuesto"].initial = 0.00
            else:
                # Para Chile, solo mostrar CLP
                self.fields["moneda"].widget = forms.Select(
                    choices=[("CLP", "CLP - Pesos Chilenos")]
                )
                self.fields["moneda"].initial = "CLP"
                # Para Chile, tasa de impuesto por defecto 19.00 (IVA)
                if not self.instance.pk:  # Solo si es nueva configuración
                    self.fields["tasa_impuesto"].initial = 19.00

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
