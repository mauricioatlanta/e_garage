
from django import forms
from dal import autocomplete
from dal_select2.widgets import ModelSelect2
from django.urls import reverse_lazy

from taller.models.vehiculos import Vehiculo
from taller.models.clientes import Cliente
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.extras_vehiculo import ColorVehiculo, MotorVehiculo, CajaVehiculo


class VehiculoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # BLINDAJE MULTI-TENANT: Extraer user y filtrar por empresa
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and hasattr(self.user, 'empresa'):
            # Filtrar clientes por empresa del usuario
            self.fields['cliente'].queryset = Cliente.objects.filter(empresa=self.user.empresa)
        else:
            # Si no hay user o empresa, no mostrar clientes
            self.fields['cliente'].queryset = Cliente.objects.none()
    
    class Meta:
        model = Vehiculo
        fields = ['cliente', 'anio', 'marca', 'modelo', 'motor', 'caja', 'patente', 'vin', 'color']
        widgets = {
            'cliente': ModelSelect2(
                url=reverse_lazy('vehiculos:autocomplete_cliente'),
                attrs={'data-placeholder': 'Buscar cliente...', 'data-minimum-input-length': 0}
            ),
            'marca': ModelSelect2(
                url=reverse_lazy('vehiculos:autocomplete_marca'),
                attrs={'data-placeholder': 'Seleccionar marca...', 'data-minimum-input-length': 0}
            ),
            'modelo': ModelSelect2(
                url=reverse_lazy('vehiculos:autocomplete_modelo'),
                forward=['marca'],
                attrs={'data-placeholder': 'Modelos según marca...', 'data-minimum-input-length': 0}
            ),
            'motor': ModelSelect2(
                url=reverse_lazy('vehiculos:autocomplete_motor'),
                forward=['modelo'],
                attrs={'data-placeholder': 'Filtrado por modelo...', 'data-minimum-input-length': 0}
            ),
            'caja': ModelSelect2(
                url=reverse_lazy('vehiculos:autocomplete_caja'),
                forward=['modelo'],
                attrs={'data-placeholder': 'Filtrado por modelo...', 'data-minimum-input-length': 0}
            ),
            'color': autocomplete.ModelSelect2(
                url=reverse_lazy('vehiculos:autocomplete_color'),
                attrs={
                    'data-placeholder': 'Selecciona o escribe un color...',
                    'data-tags': 'true',  # Permite escribir uno nuevo
                    'data-allow-clear': 'true',
                    'data-minimum-input-length': 0
                }
            )
        }
