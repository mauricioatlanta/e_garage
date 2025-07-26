from django import forms
from django.forms import ModelForm, TextInput, EmailInput, Select
from taller.models.clientes import Cliente
from taller.models.region_ciudad import TallerRegion, TallerCiudad
from utils.pais import get_regiones, get_ciudades, validar_telefono_por_pais


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'telefono', 'direccion', 'region', 'ciudad', 'email']
        # Excluimos el campo empresa ya que se asigna automáticamente en la vista

    def __init__(self, *args, **kwargs):
        # Extraer el usuario para obtener el país
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Determinar el país del usuario
        pais = 'CL'  # Default Chile
        if self.user and hasattr(self.user, 'empresa') and self.user.empresa.pais:
            pais = self.user.empresa.pais
        
        # Configurar placeholders y validaciones según el país
        if pais == 'US':
            self.fields['telefono'].widget.attrs.update({
                'placeholder': '(555) 123-4567',
                'pattern': r'(\+1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
            })
            self.fields['region'].label = 'State'
            self.fields['ciudad'].label = 'City'
            regiones_choices = [(r, r) for r in get_regiones('US')]
            self.fields['region'].widget = forms.Select(choices=[('', 'Select State')] + regiones_choices)
            self.fields['ciudad'].widget = forms.Select(choices=[('', 'Select City')])
            if 'region' in self.data:
                region = self.data.get('region')
                ciudades_choices = [(c, c) for c in get_ciudades('US', region)]
                self.fields['ciudad'].widget = forms.Select(choices=[('', 'Select City')] + ciudades_choices)
        else:
            self.fields['telefono'].widget.attrs.update({
                'placeholder': '+56912345678',
                'pattern': r'(\+56)?[0-9]{8,9}'
            })
            self.fields['region'].label = 'Región'
            self.fields['ciudad'].label = 'Ciudad'
            regiones_choices = [(r, r) for r in get_regiones('CL')]
            self.fields['region'].widget = forms.Select(choices=[('', 'Seleccione Región')] + regiones_choices)
            self.fields['ciudad'].widget = forms.Select(choices=[('', 'Seleccione Ciudad')])
            if 'region' in self.data:
                region = self.data.get('region')
                ciudades_choices = [(c, c) for c in get_ciudades('CL', region)]
                self.fields['ciudad'].widget = forms.Select(choices=[('', 'Seleccione Ciudad')] + ciudades_choices)

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            # Determinar el país del usuario
            pais = 'CL'  # Default Chile
            if self.user and hasattr(self.user, 'empresa') and self.user.empresa.pais:
                pais = self.user.empresa.pais
            
            # Validar formato según el país
            if not validar_telefono_por_pais(telefono, pais):
                if pais == 'US':
                    raise forms.ValidationError('Enter a valid US phone number format: (555) 123-4567')
                else:
                    raise forms.ValidationError('Ingrese un formato válido de teléfono chileno: +56912345678')
        return telefono

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre']
        return nombre.capitalize() if nombre else nombre

    def clean_apellido(self):
        apellido = self.cleaned_data.get('apellido', '')
        return apellido.capitalize() if apellido else apellido

    def clean_direccion(self):
        direccion = self.cleaned_data.get('direccion', '')
        return direccion.title() if direccion else direccion

