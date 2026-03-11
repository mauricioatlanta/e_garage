"""
Formulario de cierre de vehículo de desarme.
"""

from django import forms


class CierreVehiculoDesarmeForm(forms.Form):
    """Cierre lógico: fecha, peso final, valor por kg, observación."""

    fecha_cierre = forms.DateField(
        label="Fecha de cierre",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )
    peso_final_kg = forms.DecimalField(
        label="Peso final (kg)",
        min_value=0,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    valor_final_por_kg = forms.DecimalField(
        label="Valor por kg",
        min_value=0,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    observaciones = forms.CharField(
        label="Observaciones",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )
