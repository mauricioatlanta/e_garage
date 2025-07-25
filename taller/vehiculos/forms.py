from dal import autocomplete
from django import forms
from taller.models.vehiculos import Vehiculo
from taller.models.extras_vehiculo import ColorVehiculo, MotorVehiculo, CajaVehiculo
from taller.utils.pais_utils import get_marcas_por_pais, validar_patente_por_pais


class VehiculoForm(forms.ModelForm):
    anio = forms.TypedChoiceField(
        choices=[(str(y), str(y)) for y in range(2026, 1959, -1)],
        coerce=int,
        label="Año"
    )

    def __init__(self, *args, **kwargs):
        # Extraer el usuario del contexto
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 🌎 Filtrar marcas según país del usuario
        if self.user and hasattr(self.user, 'empresa'):
            # Configurar queryset de marcas según país
            if self.user.empresa.pais == 'US':
                # Para USA, usar MarcaVehiculo
                from taller.models.marcas_usa import MarcaVehiculo
                marcas_disponibles = MarcaVehiculo.objects.filter(
                    pais_origen='USA', 
                    activa=True
                ).order_by('nombre')
                
                # Actualizar widget para usar las marcas USA
                self.fields['marca'].widget = autocomplete.ModelSelect2(
                    url='vehiculos:autocomplete_marca_usa',
                    attrs={
                        'data-placeholder': 'Select a US vehicle brand...',
                        'data-minimum-input-length': 0
                    }
                )
            else:
                # Para Chile, usar Marca tradicional
                self.fields['marca'].widget = autocomplete.ModelSelect2(
                    url='autocomplete:autocomplete_marca',
                    attrs={
                        'data-placeholder': 'Selecciona una marca chilena...',
                        'data-minimum-input-length': 0
                    }
                )
            
            # 📋 Personalizar placeholder de patente según país
            if self.user.empresa.pais == 'US':
                self.fields['patente'].widget.attrs.update({
                    'placeholder': 'License plate (e.g., ABC123)',
                    'pattern': '[A-Z0-9]{2,8}',
                    'title': 'US license plate format'
                })
            else:
                self.fields['patente'].widget.attrs.update({
                    'placeholder': 'Patente (ej: AA1234)',
                    'pattern': '[A-Z]{2,4}[0-9]{2,4}',
                    'title': 'Formato patente chilena'
                })

    def clean_patente(self):
        """Validar formato de patente según país"""
        patente = self.cleaned_data.get('patente', '').upper()
        
        if self.user and hasattr(self.user, 'empresa'):
            pais = self.user.empresa.pais
            if not validar_patente_por_pais(patente, pais):
                if pais == 'US':
                    raise forms.ValidationError(
                        "Invalid US license plate format. Use letters and numbers (2-8 characters)."
                    )
                else:
                    raise forms.ValidationError(
                        "Formato de patente chilena inválido. Use formato AA1234 o ABCD12."
                    )
        
        return patente

    class Meta:
        model = Vehiculo
        fields = ['cliente', 'patente', 'marca', 'modelo', 'anio', 'color', 'vin', 'motor', 'caja']
        widgets = {
            'cliente': autocomplete.ModelSelect2(
                url='vehiculos:autocomplete_cliente',
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
                url='vehiculos:autocomplete_color',
                attrs={
                    'data-placeholder': 'Selecciona o escribe un color...',
                    'data-tags': 'true',
                    'data-allow-clear': 'true',
                    'data-minimum-input-length': 0
                }
            ),
            'motor': autocomplete.ModelSelect2(
                url='vehiculos:autocomplete_motor',
                forward=['modelo'],
                attrs={
                    'data-placeholder': 'Escribe para buscar o agregar un nuevo motor...',
                    'data-minimum-input-length': 0,
                    'data-tags': 'true'
                }
            ),
            'caja': autocomplete.ModelSelect2(
                url='vehiculos:autocomplete_caja',
                forward=['modelo'],
                attrs={
                    'data-placeholder': 'Escribe para buscar o agregar una nueva caja...',
                    'data-minimum-input-length': 0,
                    'data-tags': 'true'
                }
            ),
        }
