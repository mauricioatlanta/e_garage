from django import forms
from .models import Documento
from .lineas_documento import LineaDocumento

class DocumentoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        if self.empresa:
            # Filtrar los queryset por empresa si está disponible
            from taller.models.clientes import Cliente
            from taller.models.vehiculos import Vehiculo
            from taller.models.tecnico import Tecnico
            
            if hasattr(self.fields['cliente'], 'queryset'):
                self.fields['cliente'].queryset = Cliente.objects.filter(empresa=self.empresa)
            if hasattr(self.fields['vehiculo'], 'queryset'):
                self.fields['vehiculo'].queryset = Vehiculo.objects.filter(empresa=self.empresa)
            if hasattr(self.fields['tecnico_responsable'], 'queryset'):
                self.fields['tecnico_responsable'].queryset = Tecnico.objects.filter(empresa=self.empresa)
    
    class Meta:
        model = Documento
        fields = ["tipo", "numero", "fecha_emision", "cliente", "vehiculo", "tecnico_responsable", "moneda", "country", "descuento"]

class LineaDocumentoForm(forms.ModelForm):
    class Meta:
        model = LineaDocumento
        fields = ["item_type", "descripcion", "qty", "unit_price"]
