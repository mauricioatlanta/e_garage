from django import forms
from taller.models import ConfiguracionEmpresa

class ConfiguracionEmpresaForm(forms.ModelForm):
    """Formulario para configuración de empresa"""
    
    class Meta:
        model = ConfiguracionEmpresa
        fields = ['nombre_publico', 'tagline', 'logo', 'moneda', 'iva_porcentaje', 
                 'aplicar_iva_por_defecto', 'dividir_por_tecnico_por_defecto', 'brand_color']
        widgets = {
            'nombre_publico': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de su empresa'
            }),
            'tagline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Su eslogan aquí (opcional)'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'moneda': forms.Select(attrs={
                'class': 'form-select'
            }),
            'iva_porcentaje': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100'
            }),
            'aplicar_iva_por_defecto': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'dividir_por_tecnico_por_defecto': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'brand_color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que los campos con valores por defecto no sean requeridos
        self.fields['moneda'].required = False
        self.fields['iva_porcentaje'].required = False
        self.fields['aplicar_iva_por_defecto'].required = False
        self.fields['dividir_por_tecnico_por_defecto'].required = False
        self.fields['brand_color'].required = False


class CompanyInfoForm(forms.ModelForm):
    """Formulario específico solo para información de empresa (nombre, logo, tagline)"""
    
    class Meta:
        model = ConfiguracionEmpresa
        fields = ['nombre_publico', 'tagline', 'logo', 'iva_porcentaje', 'aplicar_iva_por_defecto']
        widgets = {
            'nombre_publico': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de su empresa'
            }),
            'tagline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Su eslogan aquí (opcional)'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'iva_porcentaje': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': '19.00'
            }),
            'aplicar_iva_por_defecto': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer que los campos no sean requeridos
        self.fields['iva_porcentaje'].required = False
        self.fields['aplicar_iva_por_defecto'].required = False
        
        # Personalizar labels según el país de la empresa
        if self.instance and hasattr(self.instance, 'empresa') and self.instance.empresa:
            if self.instance.empresa.pais == 'US':
                self.fields['iva_porcentaje'].label = 'Tax Rate (%)'
                self.fields['aplicar_iva_por_defecto'].label = 'Apply Tax by Default'
            else:
                self.fields['iva_porcentaje'].label = 'IVA (%)'
                self.fields['aplicar_iva_por_defecto'].label = 'Aplicar IVA por Defecto'
    
    def clean_tagline(self):
        # Si viene vacío, devolver "" (no devolver self.instance.tagline ni None)
        value = self.cleaned_data.get("tagline", "")
        return value or ""

