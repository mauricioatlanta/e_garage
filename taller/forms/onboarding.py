from django.utils.translation import gettext_lazy as _
from django import forms
from taller.models.empresa import Empresa
from taller.models.configuracion import ConfiguracionEmpresa


class OnboardingIdentidadForm(forms.ModelForm):
    """Paso 1: Identidad de la empresa"""

    lema = forms.CharField(required=False, label=_("Lema"))

    class Meta:
        model = Empresa
        fields = ["nombre_taller", "logo"]
        labels = {
            "nombre_taller": _("Nombre del Taller"),
            "logo": _("Logo"),
        }
        widgets = {
            "nombre_taller": forms.TextInput(
                attrs={
                    "class": "form-control futuristic-input",
                    "placeholder": _("Ej: Taller Mecánico Pro"),
                }
            ),
            "logo": forms.FileInput(attrs={"class": "form-control futuristic-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and getattr(self.instance, "pk", None):
            try:
                config = getattr(self.instance, "config", None)
                if config:
                    self.fields["lema"].initial = getattr(config, "tagline", "")
            except Exception:
                pass

    def save(self, commit=True):
        empresa = super().save(commit=commit)
        lema = (self.cleaned_data.get("lema") or "").strip()
        if commit:
            config, _ = ConfiguracionEmpresa.objects.get_or_create(empresa=empresa)
            config.tagline = lema
            config.save(update_fields=["tagline"])
        return empresa


class OnboardingFiscalForm(forms.ModelForm):
    """Paso 2: Configuración Fiscal"""

    class Meta:
        model = ConfiguracionEmpresa
        fields = ["moneda", "tasa_impuesto"]
        labels = {
            "moneda": _("Moneda"),
            "tasa_impuesto": _("Tasa de Impuesto (%)"),
        }
        widgets = {
            "moneda": forms.TextInput(
                attrs={"class": "form-control futuristic-input", "placeholder": _("Ej: CLP, USD")}
            ),
            "tasa_impuesto": forms.NumberInput(
                attrs={"class": "form-control futuristic-input", "step": "0.01"}
            ),
        }


class OnboardingContactoForm(forms.ModelForm):
    """Paso 3: Información de contacto"""

    sitio_web = forms.URLField(
        required=False,
        label=_("Sitio Web"),
        widget=forms.URLInput(
            attrs={
                "class": "form-control futuristic-input",
                "placeholder": _("https://www.tu-taller.com"),
            }
        ),
    )

    class Meta:
        model = Empresa
        fields = ["telefono", "email", "direccion"]
        labels = {
            "telefono": _("Teléfono"),
            "email": _("Email"),
            "direccion": _("Dirección"),
        }
        widgets = {
            "telefono": forms.TextInput(
                attrs={
                    "class": "form-control futuristic-input",
                    "placeholder": _("Ej: +56912345678"),
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control futuristic-input",
                    "placeholder": _("contacto@taller.com"),
                }
            ),
            "direccion": forms.TextInput(
                attrs={
                    "class": "form-control futuristic-input",
                    "placeholder": _("Calle, Número, Ciudad"),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, "config"):
            self.fields["sitio_web"].initial = self.instance.config.sitio_web

    def save(self, commit=True):
        empresa = super().save(commit=commit)
        sitio_web = self.cleaned_data.get("sitio_web")
        if commit:
            config, _ = ConfiguracionEmpresa.objects.get_or_create(empresa=empresa)
            config.sitio_web = sitio_web
            config.save()
        return empresa
