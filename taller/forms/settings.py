from django import forms

from ..models import ConfiguracionEmpresa


class ConfigEmpresaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionEmpresa
        fields = [
            "nombre_publico",
            "logo",
            "direccion",
            "telefono",
            "email_contacto",
            "moneda",
            "tasa_impuesto",
            "aplicar_impuesto_por_defecto",
            "dividir_por_tecnico",
            "brand_color",
            "tecnico_por_defecto",
        ]
        widgets = {
            "nombre_publico": forms.TextInput(attrs={"class": "form-control"}),
            "logo": forms.FileInput(attrs={"class": "form-control"}),
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
            "moneda": forms.Select(
                choices=[("CLP", "Peso Chileno"), ("USD", "Dólar Estadounidense")],
                attrs={"class": "form-select"},
            ),
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
            "tecnico_por_defecto": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar técnicos por empresa si tenemos una instancia
        if self.instance and self.instance.empresa:
            self.fields["tecnico_por_defecto"].queryset = (
                self.instance.empresa.tecnicos.all()
            )
