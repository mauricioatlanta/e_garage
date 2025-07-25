from django import forms
from taller.models.compra import Compra

class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = '__all__'
