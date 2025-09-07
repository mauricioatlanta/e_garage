# Este archivo debe contener solo formularios, no modelos.
from dal import autocomplete
from django import forms

from taller.models.clientes import Cliente
from taller.models.documento import Documento


class DocumentoForm(forms.ModelForm):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        widget=autocomplete.ModelSelect2(
            url="taller:autocomplete:autocomplete_cliente",
            attrs={
                "data-placeholder": "🔍 Buscar cliente...",
                "data-minimum-input-length": 2,
            },
        ),
        required=False,
    )

    class Meta:
        model = Documento
        fields = "__all__"
