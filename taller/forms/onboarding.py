from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django import forms
from taller.models.empresa import Empresa
from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.tecnico import ROL_SUGERENCIAS, Tecnico
from taller.services.onboarding_service import OnboardingService


class OnboardingIdentidadForm(forms.ModelForm):
    """Paso 1: Identidad de la empresa"""

    nombre_taller = forms.CharField(required=True, label=_("Nombre del Taller"))
    lema = forms.CharField(required=False, label=_("Lema"))
    telefono = forms.CharField(required=True, label=_("Teléfono"))
    email = forms.EmailField(required=True, label=_("Email de contacto"))
    direccion = forms.CharField(required=True, label=_("Dirección"))
    rubro_principal = forms.ChoiceField(
        choices=ConfiguracionEmpresa.RUBRO_CHOICES,
        initial="WORKSHOP",
        required=True,
        label=_("Tipo de negocio"),
        widget=forms.Select(attrs={"class": "form-control onb-control"}),
    )

    class Meta:
        model = Empresa
        fields = ["nombre_taller", "telefono", "email", "direccion", "logo"]
        labels = {
            "nombre_taller": _("Nombre del Taller"),
            "telefono": _("Teléfono"),
            "email": _("Email de contacto"),
            "direccion": _("Dirección"),
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

    def clean_nombre_taller(self):
        nombre = (self.cleaned_data.get("nombre_taller") or "").strip()
        empresa = self.instance
        if empresa is not None:
            empresa.nombre_taller = nombre
        user = getattr(empresa, "user", None)
        if not nombre or OnboardingService.is_placeholder_business_name(empresa, user=user):
            raise forms.ValidationError(
                _("Ingresa el nombre real de tu negocio, no un nombre genérico.")
            )
        return nombre

    def clean_telefono(self):
        telefono = (self.cleaned_data.get("telefono") or "").strip()
        if not OnboardingService.is_valid_phone(telefono):
            raise forms.ValidationError(
                _(
                    "El teléfono es obligatorio y debe tener al menos 8 caracteres. "
                    "Solo números, espacios, guiones, + y paréntesis."
                )
            )
        return telefono

    def clean_direccion(self):
        direccion = (self.cleaned_data.get("direccion") or "").strip()
        if not direccion:
            raise forms.ValidationError(_("La dirección es obligatoria."))
        return direccion

    def save(self, commit=True):
        empresa = super().save(commit=commit)
        lema = (self.cleaned_data.get("lema") or "").strip()
        rubro = self.cleaned_data.get("rubro_principal")
        if commit:
            config, _ = ConfiguracionEmpresa.objects.get_or_create(empresa=empresa)
            config.tagline = lema
            config.rubro_principal = rubro
            config.telefono = empresa.telefono
            config.email_contacto = empresa.email
            config.direccion = empresa.direccion
            if rubro and rubro not in (config.rubros or []):
                config.rubros = [rubro] + list(config.rubros or [])
            if config.modules_configured_at is None:
                config.modules_configured_at = timezone.now()
            config.save(
                update_fields=[
                    "tagline",
                    "rubro_principal",
                    "rubros",
                    "telefono",
                    "email_contacto",
                    "direccion",
                    "modules_configured_at",
                ]
            )
        return empresa


class OnboardingEquipoForm(forms.ModelForm):
    """Paso 2: personal operativo mínimo."""

    rol = forms.CharField(
        required=True,
        label=_("Rol"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control onb-control",
                "placeholder": _("Ej: Técnico, Vendedor, Mecánico General"),
                "list": "rol-sugerencias",
            }
        ),
    )

    class Meta:
        model = Tecnico
        fields = ["nombre", "telefono", "direccion", "rol"]
        labels = {
            "nombre": _("Nombre completo"),
            "telefono": _("Teléfono"),
            "direccion": _("Dirección"),
            "rol": _("Rol"),
        }
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control onb-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control onb-control"}),
            "direccion": forms.TextInput(attrs={"class": "form-control onb-control"}),
        }

    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop("empresa", None)
        super().__init__(*args, **kwargs)
        if self.empresa is not None:
            self.instance.empresa = self.empresa
        self.rol_sugerencias = ROL_SUGERENCIAS

    def clean(self):
        cleaned_data = super().clean()
        nombre = cleaned_data.get("nombre")
        telefono = cleaned_data.get("telefono")
        try:
            OnboardingService.validate_tecnico_data(nombre, telefono)
        except forms.ValidationError as exc:
            for field, messages in exc.message_dict.items():
                for message in messages:
                    self.add_error(field, message)
        rol = (cleaned_data.get("rol") or "").strip()
        if not rol:
            self.add_error("rol", _("El rol es obligatorio."))
        if self.empresa and nombre:
            qs = Tecnico.objects.filter(empresa=self.empresa, nombre__iexact=nombre.strip())
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error(
                    "nombre",
                    _("Ya existe un técnico con ese nombre en tu empresa."),
                )
        return cleaned_data

    def save(self, commit=True):
        tecnico = super().save(commit=False)
        if self.empresa is not None:
            tecnico.empresa = self.empresa
        tecnico.activo = True
        if commit:
            tecnico.full_clean()
            tecnico.save()
        return tecnico


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
