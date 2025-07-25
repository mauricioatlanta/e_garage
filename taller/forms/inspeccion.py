from django import forms
from taller.models.inspeccion import Inspeccion

class InspeccionForm(forms.ModelForm):
    class Meta:
        model = Inspeccion
        fields = '__all__'
