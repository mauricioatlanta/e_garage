from django import forms
from .models import Estado

class UbicacionForm(forms.Form):
    estado = forms.ModelChoiceField(queryset=Estado.objects.all(), empty_label="Selecciona un estado", label="Estado")
    ciudad = forms.CharField(label="Ciudad", widget=forms.TextInput(attrs={'list': 'ciudades-list'}))
    zip_code = forms.CharField(label="Código Postal", widget=forms.TextInput(attrs={'readonly': 'readonly'}))
