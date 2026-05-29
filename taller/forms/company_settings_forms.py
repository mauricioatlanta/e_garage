from django import forms
from django.utils.translation import gettext_lazy as _

from taller.models.company_settings import CompanySettings


class CompanyProfileForm(forms.ModelForm):
    """Formulario para perfil de empresa (nombre, logo, contacto, datos fiscales)"""

    class Meta:
        model = CompanySettings
        fields = [
            "company_name",
            "tagline",
            "logo",
            "address",
            "phone",
            "email",
            "website",
            "tax_id",
            "business_license",
        ]
        widgets = {
            "company_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Nombre de la empresa"),
                }
            ),
            "tagline": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Eslogan o frase descriptiva"),
                }
            ),
            "logo": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/png,image/jpeg,image/jpg,image/svg+xml,image/webp,image/jfif",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": _("Dirección completa del taller"),
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("+56 9 1234 5678"),
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("contacto@empresa.com"),
                }
            ),
            "website": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("https://empresa.com"),
                }
            ),
            "tax_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("RUT/NIT/Tax ID"),
                }
            ),
            "business_license": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Licencia comercial"),
                }
            ),
        }
        labels = {
            "company_name": _("Nombre de la empresa"),
            "tagline": _("Eslogan"),
            "logo": _("Logo de la empresa"),
            "address": _("Dirección"),
            "phone": _("Teléfono"),
            "email": _("Email"),
            "website": _("Sitio web"),
            "tax_id": _("RUT/NIT/Tax ID"),
            "business_license": _("Licencia comercial"),
        }
        help_texts = {
            "company_name": _("Nombre que aparecerá en lugar de 'eGarage'"),
            "tagline": _("Texto corto que aparece bajo el nombre"),
            "logo": _("Logo personalizado (PNG, JPG, JPEG, SVG, WEBP)"),
            "address": _("Dirección completa del taller"),
            "phone": _("Teléfono principal"),
            "email": _("Email de contacto"),
            "website": _("URL del sitio web (opcional)"),
            "tax_id": _("Número de identificación fiscal"),
            "business_license": _("Número de licencia o registro comercial"),
        }


class FinancialSettingsForm(forms.ModelForm):
    """Formulario para configuración financiera (moneda, impuestos)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Chile: IVA 19% por defecto, pero no bloquear guardado si el campo no llega en POST.
        if "tax_rate" in self.fields:
            self.fields["tax_rate"].required = False
            self.fields["tax_rate"].initial = 19.00

        if self.instance and getattr(self.instance, "tax_rate", None) in (None, ""):
            self.instance.tax_rate = 19.00


    class Meta:
        model = CompanySettings
        fields = [
            "currency",
            "tax_rate",
            "apply_tax_by_default",
        ]
        widgets = {
            "currency": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "tax_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "apply_tax_by_default": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }
        labels = {
            "currency": _("Moneda"),
            "tax_rate": _("Tasa de impuesto"),
            "apply_tax_by_default": _("Aplicar impuesto por defecto"),
        }
        help_texts = {
            "currency": _("Moneda utilizada en los documentos"),
            "tax_rate": _("Tasa de impuesto por defecto (ej: 19.00 para Chile, 0.00 para USA)"),
            "apply_tax_by_default": _("Aplicar impuesto automáticamente en nuevos documentos"),
        }


class ThemeSettingsForm(forms.ModelForm):
    """Formulario para configuración de tema y colores"""

    class Meta:
        model = CompanySettings
        fields = [
            "primary_color",
            "secondary_color",
            "separate_by_technician",
        ]
        widgets = {
            "primary_color": forms.TextInput(
                attrs={
                    "type": "color",
                    "class": "form-control form-control-color",
                }
            ),
            "secondary_color": forms.TextInput(
                attrs={
                    "type": "color",
                    "class": "form-control form-control-color",
                }
            ),
            "separate_by_technician": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }
        labels = {
            "primary_color": _("Color primario"),
            "secondary_color": _("Color secundario"),
            "separate_by_technician": _("Separar por técnico"),
        }
        help_texts = {
            "primary_color": _("Color principal del tema (formato hexadecimal, ej: #FF0000)"),
            "secondary_color": _("Color secundario del tema (formato hexadecimal)"),
            "separate_by_technician": _("Mostrar reportes separados por técnico"),
        }

    def clean_primary_color(self):
        """Asegura que el color primario tenga formato hexadecimal"""
        color = self.cleaned_data.get("primary_color", "")
        if color and not color.startswith("#"):
            return f"#{color}"
        return color

    def clean_secondary_color(self):
        """Asegura que el color secundario tenga formato hexadecimal"""
        color = self.cleaned_data.get("secondary_color", "")
        if color and not color.startswith("#"):
            return f"#{color}"
        return color


class CompanySettingsForm(forms.ModelForm):
    """Formulario completo de configuración de empresa (para fallback)"""

    class Meta:
        model = CompanySettings
        fields = [
            "company_name",
            "tagline",
            "logo",
            "address",
            "phone",
            "email",
            "website",
            "tax_id",
            "business_license",
            "currency",
            "tax_rate",
            "apply_tax_by_default",
            "primary_color",
            "secondary_color",
            "separate_by_technician",
            "invoice_prefix",
            "quote_prefix",
            "work_order_prefix",
            "about_text",
            "terms_and_conditions",
        ]
        widgets = {
            "company_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Nombre de la empresa"),
                }
            ),
            "tagline": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Eslogan o frase descriptiva"),
                }
            ),
            "logo": forms.FileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/png,image/jpeg,image/jpg,image/svg+xml,image/webp,image/jfif",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": _("Dirección completa del taller"),
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("+56 9 1234 5678"),
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("contacto@empresa.com"),
                }
            ),
            "website": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("https://empresa.com"),
                }
            ),
            "tax_id": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("RUT/NIT/Tax ID"),
                }
            ),
            "business_license": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Licencia comercial"),
                }
            ),
            "currency": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "tax_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "apply_tax_by_default": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "primary_color": forms.TextInput(
                attrs={
                    "type": "color",
                    "class": "form-control form-control-color",
                }
            ),
            "secondary_color": forms.TextInput(
                attrs={
                    "type": "color",
                    "class": "form-control form-control-color",
                }
            ),
            "separate_by_technician": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
            "invoice_prefix": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("FAC"),
                }
            ),
            "quote_prefix": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("COT"),
                }
            ),
            "work_order_prefix": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("OT"),
                }
            ),
            "about_text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": _("Descripción de la empresa"),
                }
            ),
            "terms_and_conditions": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": _("Términos y condiciones"),
                }
            ),
        }
