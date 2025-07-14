from django import forms
from taller.models.tienda import Tienda

class TiendaForm(forms.ModelForm):
    class Meta:
        model = Tienda
        fields = ['nombre', 'direccion', 'telefono', 'email', 'sitio_web', 'ciudad', 'region', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la tienda'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56 9 1234 5678'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@tienda.com'}),
            'sitio_web': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.tienda.com'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ciudad'}),
            'region': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Región'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
