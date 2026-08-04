from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django import forms
from taller.models.empresa import Empresa
from taller.models.configuracion import ConfiguracionEmpresa


class OnboardingIdentidadForm(forms.ModelForm):
    """Paso 1: Identidad de la empresa"""

    nombre_taller = forms.CharField(required=False, label=_("Nombre del Taller"))
    lema = forms.CharField(required=False, label=_("Lema"))
    rubro_principal = forms.ChoiceField(
        choices=ConfiguracionEmpresa.RUBRO_CHOICES,
        initial="WORKSHOP",
        required=False,
        label=_("Tipo de negocio"),
        widget=forms.Select(attrs={"class": "form-control onb-control"}),
    )

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
                    self.fields["rubro_principal"].initial = getattr(
                        config, "rubro_principal", "WORKSHOP"
                    )
            except Exception:
                pass

    def save(self, commit=True):
        nombre_taller = (self.cleaned_data.get("nombre_taller") or "").strip()
        if not nombre_taller and self.instance and getattr(self.instance, "pk", None):
            self.cleaned_data["nombre_taller"] = self.instance.nombre_taller

        empresa = super().save(commit=commit)
        lema = (self.cleaned_data.get("lema") or "").strip()
        rubro = self.cleaned_data.get("rubro_principal") or "WORKSHOP"
        if commit:
            config, _ = ConfiguracionEmpresa.objects.get_or_create(empresa=empresa)
            config.tagline = lema
            config.rubro_principal = rubro
            if config.modules_configured_at is None:
                config.modules_configured_at = timezone.now()
            config.save(update_fields=["tagline", "rubro_principal", "modules_configured_at"])
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
