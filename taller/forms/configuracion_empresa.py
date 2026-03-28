from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import ClearableFileInput

from taller.models import ConfiguracionEmpresa
from taller.utils.country_config import get_country_config

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

        # Detectar país y aplicar defaults usando una sola fuente (country_config)
        country_code = None
        if request:
            try:
                from taller.utils.empresa import get_active_empresa

                empresa = get_active_empresa(request)
                if empresa:
                    country_code = getattr(empresa, "pais", None)
            except Exception:
                pass

            if not country_code:
                path = (getattr(request, "path", "") or "").lower()
                if path.startswith("/us/"):
                    country_code = "US"
                elif path.startswith("/cl/"):
                    country_code = "CL"

        config = get_country_config(country_code)
        currency = config.get("currency")
        tax_rate = config.get("tax_rate", 0.0)

        if currency:
            self.fields["moneda"].widget = forms.Select(choices=[(currency, currency)])
            self.fields["moneda"].initial = currency

        if not self.instance.pk:
            self.fields["tasa_impuesto"].initial = tax_rate

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")
        if not logo:
            return logo
        if logo.size > MAX_LOGO_MB * 1024 * 1024:
            raise ValidationError(f"El logo no puede exceder {MAX_LOGO_MB}MB.")
        if hasattr(logo, "content_type") and logo.content_type not in ALLOWED_IMAGE_MIMES:
            raise ValidationError("Formato de imagen no soportado.")
        return logo
