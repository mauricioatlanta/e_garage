from django import forms
from dal import autocomplete
from taller.models.documento import Documento
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from django.db import models


Documento = Documento

class DetalleDocumento(models.Model):
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='detalles')
    tipo_item = models.CharField(max_length=50)
    nombre = models.CharField(max_length=255)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cantidad = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, default=0)

    def save(self, *args, **kwargs):
        self.subtotal = self.precio_venta * self.cantidad
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo_item}: {self.nombre}"

class DocumentoForm(forms.ModelForm):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='autocomplete:autocomplete_cliente',
            attrs={'data-placeholder': 'Buscar cliente...'}
        )
    )
    vehiculo = forms.ModelChoiceField(
        queryset=Vehiculo.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='autocomplete:autocomplete_vehiculo',
            forward=['cliente'],
            attrs={'data-placeholder': 'Filtrar vehículo por cliente'}
        )
    )

    class Meta:
        model = Documento
        fields = [
            'tipo_documento',
            'numero_documento',
            'fecha',
            'cliente',
            'vehiculo',
            'kilometraje',
            'observaciones',
        ]
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        }
