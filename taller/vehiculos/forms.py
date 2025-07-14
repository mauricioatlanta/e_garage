from dal import autocomplete
from dal import autocomplete
from django import forms
from taller.models.vehiculos import Vehiculo
from taller.models.extras_vehiculo import ColorVehiculo, MotorVehiculo, CajaVehiculo


class VehiculoForm(forms.ModelForm):
    anio = forms.TypedChoiceField(
        choices=[(str(y), str(y)) for y in range(2026, 1959, -1)],
        coerce=int,
        label="Año"
    )

    class Meta:
        model = Vehiculo
        fields = ['cliente', 'patente', 'marca', 'modelo', 'anio', 'color', 'vin', 'motor', 'caja']
        widgets = {
            'cliente': autocomplete.ModelSelect2(
                url='autocomplete:autocomplete_cliente',
                attrs={
                    'data-placeholder': 'Escribe para buscar o ver sugerencias...',
                    'data-minimum-input-length': 0
                }
            ),
            'marca': autocomplete.ModelSelect2(
                url='autocomplete:autocomplete_marca',
                attrs={
                    'data-placeholder': 'Escribe para buscar o ver sugerencias...',
                    'data-minimum-input-length': 0
                }
            ),
            'modelo': autocomplete.ModelSelect2(
                url='autocomplete:autocomplete_modelo',
                forward=['marca'],
                attrs={
                    'data-placeholder': 'Escribe para buscar o ver sugerencias...',
                    'data-minimum-input-length': 0
                }
            ),
            'color': autocomplete.ModelSelect2(
                url='autocomplete:autocomplete_color',
                attrs={
                    'data-placeholder': 'Selecciona o escribe un color...',
                    'data-tags': 'true',
                    'data-allow-clear': 'true',
                    'data-minimum-input-length': 0
                }
            ),
            'motor': autocomplete.ModelSelect2(
                url='autocomplete:autocomplete_motor',
                forward=['modelo'],
                attrs={
                    'data-placeholder': 'Escribe para buscar o agregar un nuevo motor...',
                    'data-minimum-input-length': 0,
                    'data-tags': 'true'
                }
            ),
            'caja': autocomplete.ModelSelect2(
                url='autocomplete:autocomplete_caja',
                forward=['modelo'],
                attrs={
                    'data-placeholder': 'Escribe para buscar o agregar una nueva caja...',
                    'data-minimum-input-length': 0,
                    'data-tags': 'true'
                }
            ),
        }
