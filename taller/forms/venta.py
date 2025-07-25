from django import forms
from taller.models.venta import Venta

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = '__all__'
