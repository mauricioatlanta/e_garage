from django import forms
from taller.models.documento import Documento

class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = '__all__'
