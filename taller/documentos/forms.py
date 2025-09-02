from django import forms
from .models import Documento
from taller.models.tecnico import Tecnico
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo

class DocumentoForm(forms.ModelForm):
    # Campo de búsqueda AJAX para clientes
    cliente_busqueda = forms.CharField(
        label="Buscar Cliente",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escribe para buscar clientes...',
            'autocomplete': 'off',
            'id': 'cliente-busqueda'
        })
    )
    
    # Campo personalizado para millas/kilometraje del vehículo
    kilometraje = forms.CharField(
        label="Kilometraje/Millas",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input input-number',
            'type': 'number',
            'step': '1',
            'min': '0',
            'placeholder': '0'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        self.user = kwargs.pop('user', None)  # Agregar soporte para user
        super().__init__(*args, **kwargs)
        
        # Configurar widgets con clases CSS
        widget_attrs = {'class': 'form-control'}
        for field_name, field in self.fields.items():
            if field_name not in ['pagado', 'cliente_busqueda']:  # Excepto campos que ya tienen widgets específicos
                if hasattr(field.widget, 'attrs'):
                    field.widget.attrs.update(widget_attrs)
        
        # Inicializar campo kilometraje con valor del vehículo
        if self.instance and hasattr(self.instance, 'vehiculo') and self.instance.vehiculo and hasattr(self.instance.vehiculo, 'millas') and self.instance.vehiculo.millas:
            self.fields['kilometraje'].initial = self.instance.vehiculo.millas
        
        # Configurar queryset de técnicos incluyendo el actual
        # Usar la empresa pasada por parámetro o la del documento
        empresa = self.empresa or (self.instance.empresa if self.instance and self.instance.empresa_id else None)
        if self.user and hasattr(self.user, 'empresa'):
            empresa = empresa or self.user.empresa
        
        if empresa:
            # Configurar querysets por empresa para evitar "Select a valid choice"
            self.fields['tecnico_responsable'].queryset = Tecnico.objects.filter(empresa=empresa)
            self.fields['cliente'].queryset = Cliente.objects.filter(empresa=empresa)
            
            # Para vehículos, mostrar solo los del cliente seleccionado o todos si no hay cliente
            if self.instance and hasattr(self.instance, 'cliente') and self.instance.cliente:
                self.fields['vehiculo'].queryset = Vehiculo.objects.filter(
                    empresa=empresa, 
                    cliente=self.instance.cliente
                )
            else:
                self.fields['vehiculo'].queryset = Vehiculo.objects.filter(empresa=empresa)
        
        # Configurar widget para el campo pagado
        self.fields['pagado'].widget = forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'switchPagado'
        })
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Manejar el campo kilometraje personalizado
        kilometraje_val = self.cleaned_data.get('kilometraje')
        if kilometraje_val:
            try:
                val = int(kilometraje_val)
                if self.instance and hasattr(self.instance, 'vehiculo') and self.instance.vehiculo:
                    v = self.instance.vehiculo
                    if val is not None:
                        if hasattr(v, "millas"):
                            v.millas = val
                            if commit:
                                v.save(update_fields=["millas"])
                        elif hasattr(v, "kilometraje"):
                            v.kilometraje = val  
                            if commit:
                                v.save(update_fields=["kilometraje"])
            except (ValueError, TypeError) as e:
                # Manejar errores de conversión de tipo
                print(f"Error al guardar kilometraje: {e}")
        
        return instance
    
    class Meta:
        model = Documento
        exclude = ('numero', 'correlativo', 'moneda', 'country', 'estado_pago', 'empresa', 'neto_repuestos', 'neto_servicios', 'neto_otros_servicios', 'descuento', 'tax_rate_applied', 'tax_amount', 'total', 'created_at')
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo'}),
            'numero': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'fecha_emision': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cliente': forms.Select(attrs={'class': 'form-select', 'id': 'id_cliente'}),
            'vehiculo': forms.Select(attrs={'class': 'form-select', 'id': 'id_vehiculo'}),
            'tecnico_responsable': forms.Select(attrs={'class': 'form-select'}),
            'kilometraje': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'moneda': forms.Select(attrs={'class': 'form-select'}),
            'pagado': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'switchPagado'}),
            'apply_vat': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': '4'}),
        }

# LineaDocumentoForm removed - using formsets instead
