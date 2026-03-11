"""
Formularios para plantillas de desarme.
"""

from django import forms

from taller.models.plantilla_desarme import PlantillaDesarme, PlantillaPieza


class PlantillaDesarmeForm(forms.ModelForm):
    """Formulario para crear/editar plantilla de desarme."""

    class Meta:
        model = PlantillaDesarme
        fields = ["nombre", "descripcion", "activa"]
        widgets = {
            "nombre": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej. Sedan, SUV"}
            ),
            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Descripción de la plantilla",
                }
            ),
            "activa": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, empresa=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.empresa = empresa
        if empresa and not self.instance.pk:
            self.instance.empresa = empresa


class PlantillaPiezaForm(forms.ModelForm):
    """Formulario para agregar/editar pieza de plantilla."""

    class Meta:
        model = PlantillaPieza
        fields = [
            "nombre_pieza",
            "orden",
            "codigo_base",
            "activo",
            "lado",
            "zona_mapa",
            "vista_mapa",
        ]
        widgets = {
            "nombre_pieza": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ej. Puerta delantera izquierda"}
            ),
            "orden": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "codigo_base": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Código opcional"}
            ),
            "activo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "lado": forms.Select(
                attrs={"class": "form-select"},
                choices=[
                    ("", "—"),
                    ("left", "Izquierdo"),
                    ("right", "Derecho"),
                    ("center", "Centro"),
                ],
            ),
            "zona_mapa": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "left_front_door, hood, etc.",
                }
            ),
            "vista_mapa": forms.Select(
                attrs={"class": "form-select"},
                choices=[
                    ("", "—"),
                    ("frontal", "Frontal"),
                    ("lateral_izq", "Lateral izquierdo"),
                    ("lateral_der", "Lateral derecho"),
                    ("trasera", "Trasera"),
                    ("motor", "Motor"),
                ],
            ),
        }
