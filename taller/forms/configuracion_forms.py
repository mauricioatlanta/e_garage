from django import forms

from taller.models import ConfiguracionEmpresa


class CompanyInfoForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionEmpresa
        fields = [
            "logo",
            "nombre_publico",
            "tagline",
            "direccion",
            "telefono",
            "email_contacto",
            "tasa_impuesto",
            "aplicar_impuesto_por_defecto",
        ]
        widgets = {
            "direccion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Dirección completa de su empresa",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Estilos opcionales
        self.fields["logo"].widget.attrs.update(
            {"class": "form-control", "accept": "image/*"}
        )
        self.fields["nombre_publico"].widget.attrs.update({"class": "form-control"})
        self.fields["tagline"].widget.attrs.update({"class": "form-control"})
        self.fields["telefono"].widget.attrs.update(
            {"class": "form-control", "placeholder": "+56 9 1234 5678"}
        )
        self.fields["email_contacto"].widget.attrs.update(
            {"class": "form-control", "placeholder": "contacto@suempresa.com"}
        )
        self.fields["tasa_impuesto"].widget.attrs.update({"class": "form-control"})
        self.fields["aplicar_impuesto_por_defecto"].widget.attrs.update(
            {"class": "form-check-input"}
        )

        # Hacer que tasa_impuesto no sea requerido y tenga valor por defecto
        self.fields["tasa_impuesto"].required = False
        if not self.instance.pk or not self.instance.tasa_impuesto:
            self.fields["tasa_impuesto"].initial = 19


class LogoUploadForm(forms.Form):
    logo = forms.ImageField(
        widget=forms.FileInput(attrs={"class": "form-control", "accept": "image/*"})
    )


class ConfiguracionEmpresaForm(forms.ModelForm):
    """Formulario para configuración de empresa completa"""

    class Meta:
        model = ConfiguracionEmpresa
        fields = [
            "nombre_publico",
            "tagline",
            "logo",
            "direccion",
            "telefono",
            "email_contacto",
            "moneda",
            "tasa_impuesto",
            "aplicar_impuesto_por_defecto",
            "dividir_por_tecnico",
            "brand_color",
        ]
        widgets = {
            "nombre_publico": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nombre de su empresa"}
            ),
            "tagline": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Su eslogan aquí (opcional)",
                }
            ),
            "logo": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
            "direccion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Dirección completa de su empresa",
                }
            ),
            "telefono": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+56 9 1234 5678"}
            ),
            "email_contacto": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "contacto@suempresa.com"}
            ),
            "moneda": forms.Select(attrs={"class": "form-select"}),
            "tasa_impuesto": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                }
            ),
            "aplicar_impuesto_por_defecto": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "dividir_por_tecnico": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "brand_color": forms.TextInput(
                attrs={"class": "form-control", "type": "color"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que los campos con valores por defecto no sean requeridos
        self.fields["moneda"].required = False
        self.fields["tasa_impuesto"].required = False
        self.fields["aplicar_impuesto_por_defecto"].required = False
        self.fields["dividir_por_tecnico"].required = False
        self.fields["brand_color"].required = False
