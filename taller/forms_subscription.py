from django import forms
from django.core.exceptions import ValidationError

class PlanPagoForm(forms.Form):
    nombre = forms.CharField(max_length=100, label="Nombre")
    email = forms.EmailField(label="Correo electrónico")
    telefono = forms.CharField(max_length=20, label="Teléfono")
    empresa = forms.CharField(max_length=100, label="Empresa", required=False)

    def clean_email(self):
        email = self.cleaned_data.get("email")
        # Aquí podrías agregar validación de unicidad si lo deseas
        return email

    def clean_telefono(self):
        telefono = self.cleaned_data.get("telefono")
        # Aquí podrías agregar validación de unicidad si lo deseas
        return telefono
