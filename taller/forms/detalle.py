from django import forms
from taller.documentos.models import DetalleDocumento



class DetalleDocumentoForm(forms.ModelForm):
    class Meta:
        model = DetalleDocumento
        fields = '__all__'  # Incluye todos los campos del modelo
