from django import forms
from taller.models.documento import ServicioDocumento

class ServicioForm(forms.ModelForm):
    class Meta:
        model = ServicioDocumento
        fields = '__all__'
