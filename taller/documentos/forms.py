from django import forms
from dal import autocomplete
from taller.models.documento import Documento
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.mecanico import Mecanico

class DocumentoForm(forms.ModelForm):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        required=True,
        widget=autocomplete.ModelSelect2(
            url='autocomplete:autocomplete_cliente',
            attrs={'data-placeholder': 'Buscar cliente...'}
        )
    )
    vehiculo = forms.ModelChoiceField(
        queryset=Vehiculo.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='autocomplete:autocomplete_vehiculo',
            forward=['cliente'],
            attrs={'data-placeholder': 'Filtrar vehículo por cliente'}
        )
    )
    mecanico = forms.ModelChoiceField(
        queryset=Mecanico.objects.all(),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='autocomplete:autocomplete_mecanico',
            attrs={
                'data-placeholder': 'Buscar o crear mecánico...',
                'data-tags': 'true',  # Permite crear nuevos
                'data-allow-clear': 'true',
                'data-minimum-input-length': '1',
            }
        ),
    )

    observaciones = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full p-4 border rounded-xl shadow-sm min-h-[120px] max-h-[300px] overflow-y-auto auto-grow-textarea',
            'rows': 4,
            'placeholder': 'Observaciones...'
        }),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from datetime import date
        if not self.initial.get('fecha') and not self.data:
            self.initial['fecha'] = date.today().strftime('%Y-%m-%d')

        # Filtrar vehículos por cliente seleccionado
        cliente_id = None
        # Si es edición, obtener de la instancia
        if self.instance and getattr(self.instance, 'cliente_id', None):
            cliente_id = self.instance.cliente_id
        # Si es POST, obtener de los datos enviados
        elif self.data.get('cliente'):
            cliente_id = self.data.get('cliente')
        elif self.initial.get('cliente'):
            cliente_id = self.initial.get('cliente')
        if cliente_id:
            # Incluir el vehículo actual aunque no pertenezca al cliente filtrado
            qs = Vehiculo.objects.filter(cliente_id=cliente_id)
            vehiculo_actual = getattr(self.instance, 'vehiculo', None)
            if vehiculo_actual and vehiculo_actual.pk:
                qs = (qs | Vehiculo.objects.filter(pk=vehiculo_actual.pk)).distinct()
            self.fields['vehiculo'].queryset = qs

    class Meta:
        model = Documento
        fields = [
            'tipo_documento', 'numero_documento', 'fecha',
            'cliente', 'vehiculo', 'kilometraje', 'observaciones', 'mecanico',
        ]
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-2 border rounded'}),
        }
