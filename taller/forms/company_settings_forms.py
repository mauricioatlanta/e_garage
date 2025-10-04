from PIL import Image

from django import forms
from django.core.validators import RegexValidator

from taller.models import CompanySettings


class CompanySettingsForm(forms.ModelForm):
    """Formulario para configuración de empresa y branding"""

    # Validador de color hexadecimal
    color_validator = RegexValidator(
        regex=r"^#[0-9A-Fa-f]{6}$",
        message="Ingrese un color válido en formato hexadecimal (ej: #FF0000)",
    )

    primary_color = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "type": "color",
                "class": "form-control form-control-color",
                "title": "Seleccionar color primario",
            }
        ),
        validators=[color_validator],
        help_text="Color principal de la interfaz",
    )

    secondary_color = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "type": "color",
                "class": "form-control form-control-color",
                "title": "Seleccionar color secundario",
            }
        ),
        validators=[color_validator],
        help_text="Color secundario de la interfaz",
    )

    company_name = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Nombre de su empresa"}
        ),
        help_text='Este nombre aparecerá en lugar de "eGarage" en toda la interfaz',
    )

    tagline = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Su eslogan aquí (opcional)"}
        ),
        help_text="Frase corta que aparece bajo el nombre de la empresa",
    )

    logo = forms.ImageField(
        required=False,
        widget=forms.FileInput(
            attrs={
                "class": "form-control",
                "accept": "image/*",
                "onchange": "previewLogo(this)",
            }
        ),
        help_text="Logo de su empresa (máximo 2MB, formatos: PNG, JPG, SVG)",
    )

    address = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Dirección completa de su taller",
            }
        ),
    )

    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "+56 9 1234 5678"}
        ),
    )

    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "contacto@mitaller.com"}
        ),
    )

    website = forms.URLField(
        required=False,
        widget=forms.URLInput(
            attrs={"class": "form-control", "placeholder": "https://www.mitaller.com"}
        ),
    )

    tax_id = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "12.345.678-9"}
        ),
        help_text="RUT, NIT o número de identificación fiscal",
    )

    business_license = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Licencia comercial o registro",
            }
        ),
    )

    currency = forms.ChoiceField(
        choices=CompanySettings._meta.get_field("currency").choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    tax_rate = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "max": "100",
                "placeholder": "19.00"
            }
        ),
        help_text="Tasa de impuesto por defecto (ej: 19.00 para Chile, 0.00 para USA)",
    )

    apply_tax_by_default = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text="Aplicar impuesto automáticamente en nuevos documentos",
    )

    separate_by_technician = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        help_text="Mostrar reportes separados por técnico",
    )

    invoice_prefix = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "FAC"}),
        help_text="Prefijo para numeración de facturas",
    )

    quote_prefix = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "COT"}),
        help_text="Prefijo para numeración de cotizaciones",
    )

    work_order_prefix = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "OT"}),
        help_text="Prefijo para numeración de órdenes de trabajo",
    )

    about_text = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Cuénteles a sus clientes sobre su taller...",
            }
        ),
        help_text="Texto que aparece en documentos y página principal",
    )

    terms_and_conditions = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": "Términos y condiciones de servicio...",
            }
        ),
        help_text="Términos que aparecen en contratos y documentos",
    )

    class Meta:
        model = CompanySettings
        exclude = ["user", "created_at", "updated_at", "timezone"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Agregar clases CSS a todos los campos
        for field_name, field in self.fields.items():
            if "class" not in field.widget.attrs:
                field.widget.attrs["class"] = "form-control"

    def clean_logo(self):
        """Validación personalizada para el logo"""
        logo = self.cleaned_data.get("logo")

        if logo:
            # Validar tamaño de archivo (máximo 2MB)
            if logo.size > 2 * 1024 * 1024:
                raise forms.ValidationError("El logo debe ser menor a 2MB")

            # Validar que sea una imagen válida
            try:
                img = Image.open(logo)
                img.verify()
            except Exception:
                raise forms.ValidationError("El archivo no es una imagen válida")

            # Restablecer el puntero del archivo
            logo.seek(0)

            # Validar dimensiones
            img = Image.open(logo)
            width, height = img.size

            if width > 1000 or height > 1000:
                raise forms.ValidationError(
                    "El logo debe ser menor a 1000x1000 píxeles"
                )

            if width < 100 or height < 100:
                raise forms.ValidationError("El logo debe ser mayor a 100x100 píxeles")

        return logo

    def clean_company_name(self):
        """Validación del nombre de empresa"""
        name = self.cleaned_data.get("company_name")
        if name and len(name.strip()) < 2:
            raise forms.ValidationError("El nombre debe tener al menos 2 caracteres")
        return name.strip() if name else name

    def clean_primary_color(self):
        """Validación del color primario"""
        color = self.cleaned_data.get("primary_color")
        if color and not color.startswith("#"):
            color = f"#{color}"
        return color

    def clean_secondary_color(self):
        """Validación del color secundario"""
        color = self.cleaned_data.get("secondary_color")
        if color and not color.startswith("#"):
            color = f"#{color}"
        return color

    def clean(self):
        """Validación general del formulario"""
        cleaned_data = super().clean()
        
        # Asegurar que los prefijos tengan valores por defecto
        if not cleaned_data.get("invoice_prefix"):
            cleaned_data["invoice_prefix"] = "FAC"
        if not cleaned_data.get("quote_prefix"):
            cleaned_data["quote_prefix"] = "COT"
        if not cleaned_data.get("work_order_prefix"):
            cleaned_data["work_order_prefix"] = "OT"
            
        return cleaned_data


class LogoUploadForm(forms.Form):
    """Formulario simple para subir solo el logo"""

    logo = forms.ImageField(
        widget=forms.FileInput(
            attrs={
                "class": "form-control",
                "accept": "image/*",
                "onchange": "previewLogo(this)",
            }
        ),
        help_text="Suba su logo (máximo 2MB, formatos: PNG, JPG, SVG)",
    )

    def clean_logo(self):
        """Validación para logo"""
        logo = self.cleaned_data.get("logo")

        if logo:
            # Validar tamaño
            if logo.size > 2 * 1024 * 1024:
                raise forms.ValidationError("El logo debe ser menor a 2MB")

            # Validar que sea imagen
            try:
                img = Image.open(logo)
                img.verify()
                logo.seek(0)  # Reset file pointer

                # Validar dimensiones
                img = Image.open(logo)
                width, height = img.size

                if width > 1000 or height > 1000:
                    raise forms.ValidationError(
                        "El logo debe ser menor a 1000x1000 píxeles"
                    )

            except Exception:
                raise forms.ValidationError("El archivo no es una imagen válida")

        return logo


class CompanyProfileForm(forms.ModelForm):
    """Formulario específico para la sección de perfil de empresa"""
    
    class Meta:
        model = CompanySettings
        fields = [
            'company_name', 'tagline', 'logo', 'address', 
            'phone', 'email', 'website', 'tax_id', 'business_license'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre de su empresa"}),
            'tagline': forms.TextInput(attrs={"class": "form-control", "placeholder": "Su eslogan aquí (opcional)"}),
            'logo': forms.FileInput(attrs={"class": "form-control", "accept": "image/*"}),
            'address': forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Dirección completa de su taller"}),
            'phone': forms.TextInput(attrs={"class": "form-control", "placeholder": "+56 9 1234 5678"}),
            'email': forms.EmailInput(attrs={"class": "form-control", "placeholder": "contacto@mitaller.com"}),
            'website': forms.URLInput(attrs={"class": "form-control", "placeholder": "https://www.mitaller.com"}),
            'tax_id': forms.TextInput(attrs={"class": "form-control", "placeholder": "12.345.678-9"}),
            'business_license': forms.TextInput(attrs={"class": "form-control", "placeholder": "Licencia comercial o registro"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer todos los campos opcionales excepto company_name
        for field_name, field in self.fields.items():
            if field_name != 'company_name':
                field.required = False


class FinancialSettingsForm(forms.ModelForm):
    """Formulario específico para la sección financiera"""
    
    class Meta:
        model = CompanySettings
        fields = ['currency', 'tax_rate', 'apply_tax_by_default']
        widgets = {
            'currency': forms.Select(attrs={"class": "form-select"}),
            'tax_rate': forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "max": "100",
                "placeholder": "19.00"
            }),
            'apply_tax_by_default': forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer todos los campos opcionales
        for field_name, field in self.fields.items():
            field.required = False


class ThemeSettingsForm(forms.ModelForm):
    """Formulario específico para la sección de tema"""
    
    class Meta:
        model = CompanySettings
        fields = ['primary_color', 'secondary_color', 'separate_by_technician']
        widgets = {
            'primary_color': forms.TextInput(attrs={
                "type": "color",
                "class": "form-control form-control-color",
                "title": "Seleccionar color primario",
            }),
            'secondary_color': forms.TextInput(attrs={
                "type": "color",
                "class": "form-control form-control-color",
                "title": "Seleccionar color secundario",
            }),
            'separate_by_technician': forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer todos los campos opcionales
        for field_name, field in self.fields.items():
            field.required = False


class BrandingPreviewForm(forms.Form):
    """Formulario para previsualizar cambios de branding"""

    company_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(
            attrs={"class": "form-control", "oninput": "updatePreview()"}
        ),
    )

    primary_color = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "type": "color",
                "class": "form-control form-control-color",
                "onchange": "updatePreview()",
            }
        )
    )

    secondary_color = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "type": "color",
                "class": "form-control form-control-color",
                "onchange": "updatePreview()",
            }
        )
    )
