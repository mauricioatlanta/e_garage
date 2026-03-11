"""
Formulario simple para aplicar plantilla a vehículo.
"""

from django import forms

from taller.models.plantilla_desarme import PlantillaDesarme


class AplicarPlantillaForm(forms.Form):
    """Selecciona una plantilla para aplicar al vehículo."""

    plantilla = forms.ModelChoiceField(
        queryset=PlantillaDesarme.objects.none(),
        empty_label="Seleccione una plantilla",
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Plantilla",
    )

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa:
            from taller.services.plantilla_desarme_service import plantillas_disponibles_para

            disponibles = plantillas_disponibles_para(empresa)
            self.fields["plantilla"].queryset = disponibles
