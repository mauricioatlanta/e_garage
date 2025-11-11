from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from taller.models import ConfiguracionEmpresa

MAX_LOGO_MB = 5
ALLOWED_IMAGE_MIMES = {"image/png", "image/jpeg", "image/webp", "image/gif"}

phone_re = RegexValidator(r"^[0-9\-\+\(\)\s]{6,20}$", "Teléfono no válido.")


def _default_tax_for_country(pais: str | None) -> float:
    if (pais or "").upper() == "CL":
        return 19.0
    return 0.0  # Global default para USA u otros; el cálculo real puede ser por documento


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
            "brand_color",
            "dividir_por_tecnico",
        ]
        widgets = {
            "nombre_publico": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "ALS AUTO REPAIR"}
            ),
            "tagline": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Your company motto"}
            ),
            "direccion": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Av. Siempre Viva 123"}
            ),
            "telefono": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+56 9 1234 5678"}
            ),
            "email_contacto": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "contacto@empresa.com"}
            ),
            "sitio_web": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "https://tu-sitio.com"}
            ),
            "moneda": forms.Select(attrs={"class": "form-select"}),
            "tasa_impuesto": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "aplicar_impuesto_por_defecto": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "brand_color": forms.TextInput(
                attrs={"type": "color", "class": "form-control form-control-color"}
            ),
            "dividir_por_tecnico": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # No requeridos
        for f in (
            "moneda",
            "tasa_impuesto",
            "aplicar_impuesto_por_defecto",
            "dividir_por_tecnico",
            "brand_color",
        ):
            self.fields[f].required = False

        # Detectar país desde la empresa (si existe relación)
        pais = None
        try:
            pais = getattr(getattr(self.instance, "empresa", None), "pais", None)
        except Exception:
            pais = None

        # Etiquetas/ayuda por país
        if (pais or "").upper() == "CL":
            self.fields["tasa_impuesto"].label = _("IVA (%)")
            self.fields["tasa_impuesto"].help_text = _(
                "Usualmente 19%. En tu lógica, el IVA aplica solo a repuestos."
            )
            if self.instance.pk is None or not self.instance.tasa_impuesto:
                self.fields["tasa_impuesto"].initial = 19.0
            if "aplicar_impuesto_por_defecto" in self.fields and self.instance.pk is None:
                self.fields["aplicar_impuesto_por_defecto"].initial = True
        else:
            self.fields["tasa_impuesto"].label = _("Sales tax por defecto (%)")
            self.fields["tasa_impuesto"].help_text = _(
                "Deja 0% si calcularás impuestos por estado a nivel de documento."
            )
            if self.instance.pk is None or not self.instance.tasa_impuesto:
                self.fields["tasa_impuesto"].initial = 0.0
            if "aplicar_impuesto_por_defecto" in self.fields and self.instance.pk is None:
                self.fields["aplicar_impuesto_por_defecto"].initial = False

    def clean_tasa_impuesto(self):
        val = self.cleaned_data.get("tasa_impuesto")
        if val in (None, ""):
            pais = None
            try:
                pais = getattr(getattr(self.instance, "empresa", None), "pais", None)
            except Exception:
                pass
            return _default_tax_for_country(pais)

        try:
            val = float(val)
        except (TypeError, ValueError):
            raise ValidationError(_("Ingrese un número válido para la tasa de impuesto."))
        if not (0.0 <= val <= 100.0):
            raise ValidationError(_("La tasa debe estar entre 0 y 100."))
        return val

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")
        if not logo:
            return logo  # no reemplazar el existente

        # Tamaño
        size_mb = getattr(logo, "size", 0) / (1024 * 1024)
        if size_mb > MAX_LOGO_MB:
            raise ValidationError(_(f"El logo excede {MAX_LOGO_MB} MB."))

        # MIME (cuando está disponible)
        content_type = getattr(logo, "content_type", None)
        if content_type and content_type.lower() not in ALLOWED_IMAGE_MIMES:
            raise ValidationError(_("Formato de imagen no permitido. Usa PNG, JPEG, WEBP o GIF."))
        return logo

    def clean_telefono(self):
        t = (self.cleaned_data.get("telefono") or "").strip()
        if t:
            phone_re(t)
        return t

    def clean_sitio_web(self):
        u = (self.cleaned_data.get("sitio_web") or "").strip()
        if u and not (u.startswith("http://") or u.startswith("https://")):
            u = "https://" + u
        return u
