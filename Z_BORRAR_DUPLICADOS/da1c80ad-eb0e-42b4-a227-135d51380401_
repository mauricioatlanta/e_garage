from django import forms

from taller.models import Tecnico


class TecnicoForm(forms.ModelForm):
    class Meta:
        model = Tecnico
        fields = ["nombre", "activo"]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Nombre del técnico / vendedor",
                }
            ),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
