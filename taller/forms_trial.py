from django import forms
from django.core.exceptions import ValidationError
from taller.models.trial import TrialRegistro

class TrialForm(forms.ModelForm):
    class Meta:
        model = TrialRegistro
        fields = ['nombre', 'email', 'telefono']

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if TrialRegistro.objects.filter(email=email).exists():
            raise ValidationError("Este correo ya ha usado la prueba gratuita.")
        return email

    def clean_telefono(self):
        telefono = self.cleaned_data.get("telefono")
        if TrialRegistro.objects.filter(telefono=telefono).exists():
            raise ValidationError("Este número ya ha usado la prueba gratuita.")
        return telefono
