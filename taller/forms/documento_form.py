# Formulario unificado y mejorado para Documento
from dal import autocomplete
from django import forms
from django.urls import reverse

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.vehiculos import Vehiculo
from taller.utils.dal_helpers import get_autocomplete_url

# Helper centralizado para namespaces de autocompletado
def _ns(country: str) -> str:
    return "usa_autocomplete" if (country or "").upper() == "US" else "cl_autocomplete"


class DocumentoForm(forms.ModelForm):
    """
    Formulario avanzado para Documento con:
    - Autocompletado DAL multi-país
    - Labels dinámicos según país
    - Filtrado multi-tenant
    - Validaciones robustas
    - IDs únicos para JavaScript
    """
    
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.none(),  # Se ajustará en __init__
        widget=autocomplete.ModelSelect2(
            url="",  # Se establecerá dinámicamente
            attrs={
                "data-placeholder": "🔍 Buscar cliente...",
                "data-minimum-input-length": 2,
            },
        ),
        required=True,
    )
    
    vehiculo = forms.ModelChoiceField(
        queryset=Vehiculo.objects.none(),  # Se ajustará en __init__
        widget=autocomplete.ModelSelect2(
            url="",  # Se establecerá dinámicamente
            forward=['cliente'],
            attrs={
                "data-placeholder": "🔍 Buscar vehículo...",
                "data-minimum-input-length": 1,
            },
        ),
        required=False,
    )

    class Meta:
        model = Documento
        fields = [
            'tipo',
            'numero', 
            'fecha_emision',
            'cliente',
            'vehiculo',
            'tecnico_responsable',
            'kilometraje',
            'millas',
            'observaciones',
            'pagado',
            'metodo_pago',
            'ult4',
            'monto_pagado',
            'saldo_pendiente',
            'fecha_pago',
            'nota_pago',
            'descuento',
        ]

    def __init__(self, *args, **kwargs):
        # Extraer argumentos personalizados
        self.user = kwargs.pop('user', None)
        self.empresa = kwargs.pop('empresa', None)
        self.country = kwargs.pop('country', 'CL')
        
        super().__init__(*args, **kwargs)
        
        # Configurar URLs de autocompletado dinámicamente
        self.fields['cliente'].widget.url = f"{_ns(self.country)}:cliente"
        self.fields['vehiculo'].widget.url = f"{_ns(self.country)}:vehiculo"
        
        # Configurar querysets filtrados por empresa
        if self.empresa:
            self.fields['cliente'].queryset = Cliente.objects.filter(empresa=self.empresa)
            self.fields['vehiculo'].queryset = Vehiculo.objects.filter(empresa=self.empresa)
            self.fields['tecnico_responsable'].queryset = self.empresa.tecnicos.all()
        
        # Configurar labels según el país
        self._configure_labels_by_country()
        
        # Configurar choices dinámicos
        self._configure_dynamic_choices()
        
        # Configurar widgets con IDs únicos para JavaScript
        self._configure_widget_ids()

    def _configure_labels_by_country(self):
        """Configura labels dinámicos según el país"""
        if self.country == "US":
            labels = {
                'tipo': "Document Type",
                'cliente': "Customer", 
                'vehiculo': "Vehicle",
                'tecnico_responsable': "Assigned Technician",
                'kilometraje': "Mileage",
                'millas': "Miles",
                'observaciones': "Notes",
                'pagado': "Paid",
                'metodo_pago': "Payment Method",
                'monto_pagado': "Amount Paid",
                'saldo_pendiente': "Outstanding Balance",
                'fecha_pago': "Payment Date",
                'nota_pago': "Payment Notes",
                'descuento': "Discount",
            }
        else:  # CL (Chile)
            labels = {
                'tipo': "Tipo de Documento",
                'cliente': "Cliente",
                'vehiculo': "Vehículo", 
                'tecnico_responsable': "Técnico Responsable",
                'kilometraje': "Kilometraje",
                'millas': "Millas",
                'observaciones': "Observaciones",
                'pagado': "Pagado",
                'metodo_pago': "Método de Pago",
                'monto_pagado': "Monto Pagado",
                'saldo_pendiente': "Saldo Pendiente",
                'fecha_pago': "Fecha de Pago",
                'nota_pago': "Nota de Pago",
                'descuento': "Descuento",
            }
        
        for field_name, label in labels.items():
            if field_name in self.fields:
                self.fields[field_name].label = label

    def _configure_dynamic_choices(self):
        """Configura choices dinámicos según el país"""
        if self.country == "US":
            self.fields['tipo'].choices = [
                ("OT", "Work Order"),
                ("PRES", "Estimate"),
                ("REC", "Receipt/Invoice"),
            ]
            
            # Millas solo en USA
            if 'millas' in self.fields:
                self.fields['millas'].required = False
                self.fields['kilometraje'].required = False
        else:  # CL (Chile)
            self.fields['tipo'].choices = [
                ("OT", "Orden de Trabajo"),
                ("PRES", "Presupuesto"),
                ("REC", "Recibo/Boleta"),
            ]
            
            # Kilometraje en Chile, millas no aplica
            if 'millas' in self.fields:
                self.fields['millas'].widget = forms.HiddenInput()
                self.fields['millas'].required = False

    def _configure_widget_ids(self):
        """Configura IDs únicos para todos los campos (para JavaScript)"""
        widget_ids = {
            'tipo': 'id_tipo',
            'numero': 'id_numero',
            'fecha_emision': 'id_fecha_emision',
            'cliente': 'id_cliente',
            'vehiculo': 'id_vehiculo',
            'tecnico_responsable': 'id_tecnico_responsable',
            'kilometraje': 'id_kilometraje',
            'millas': 'id_millas',
            'observaciones': 'id_observaciones',
            'pagado': 'id_pagado',
            'metodo_pago': 'id_metodo_pago',
            'ult4': 'id_ult4',
            'monto_pagado': 'id_monto_pagado',
            'saldo_pendiente': 'id_saldo_pendiente',
            'fecha_pago': 'id_fecha_pago',
            'nota_pago': 'id_nota_pago',
            'descuento': 'id_descuento',
        }
        
        for field_name, widget_id in widget_ids.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.setdefault("id", widget_id)

    def clean(self):
        """Validaciones robustas multi-tenant"""
        cleaned_data = super().clean()
        
        # Validar que cliente pertenece a la empresa
        cliente = cleaned_data.get('cliente')
        vehiculo = cleaned_data.get('vehiculo')
        
        if cliente and self.empresa and cliente.empresa != self.empresa:
            raise forms.ValidationError("El cliente seleccionado no pertenece a tu empresa.")
        
        if vehiculo and self.empresa and vehiculo.empresa != self.empresa:
            raise forms.ValidationError("El vehículo seleccionado no pertenece a tu empresa.")
        
        # Validar que vehículo pertenece al cliente
        if vehiculo and cliente and vehiculo.cliente != cliente:
            raise forms.ValidationError("El vehículo seleccionado no pertenece al cliente.")
        
        # Validaciones específicas por país
        if self.country == "CL":
            # En Chile, millas no debe tener valor
            if cleaned_data.get('millas'):
                raise forms.ValidationError("El campo millas no puede usarse en documentos de Chile.")
        elif self.country == "US":
            # En USA, al menos uno de kilometraje o millas debe tener valor
            if not cleaned_data.get('kilometraje') and not cleaned_data.get('millas'):
                raise forms.ValidationError("Debe especificar al menos kilometraje o millas.")
        
        return cleaned_data