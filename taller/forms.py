from taller.models.compra import Compra

class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        exclude = ['empresa']  # El campo empresa se asigna automáticamente en la vista
from taller.models.inspeccion import Inspeccion

class InspeccionForm(forms.ModelForm):
    class Meta:
        model = Inspeccion
        exclude = ['empresa']  # El campo empresa se asigna automáticamente en la vista
from taller.models.solicitud import Solicitud

class SolicitudForm(forms.ModelForm):
    class Meta:
        model = Solicitud
        exclude = ['empresa']  # El campo empresa se asigna automáticamente en la vista
from taller.models.venta import Venta

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        exclude = ['empresa']  # El campo empresa se asigna automáticamente en la vista
from taller.models.lineas_documento import LineaServicio

class ServicioForm(forms.ModelForm):
    class Meta:
        model = LineaServicio
        exclude = ['empresa']  # El campo empresa se asigna automáticamente en la vista
from taller.models.repuesto import Repuesto

class RepuestoForm(forms.ModelForm):
    repuesto = forms.ModelChoiceField(
        queryset=Repuesto.objects.none(),
        widget=autocomplete.ModelSelect2(
            url='autocomplete-repuesto',
            attrs={
                'data-placeholder': '🔍 Buscar repuesto por part number o nombre',
                'data-minimum-input-length': 1,
                'class': 'w-full',
            }
        )
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
    class Meta:
        model = Repuesto
        exclude = ['empresa']  # El campo empresa se asigna automáticamente en la vista
class VehiculoForm(forms.ModelForm):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.none(),
        widget=autocomplete.ModelSelect2(
            url='autocomplete-cliente',
            attrs={
                'data-placeholder': '🔍 Buscar cliente por nombre o RUT',
                'data-minimum-input-length': 1,
                'class': 'w-full',
            }
        )
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
    class Meta:
        model = Vehiculo
        exclude = ['empresa']  # El campo empresa se asigna automáticamente en la vista
from django import forms
from .models.empresa import Empresa

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['nombre_taller', 'logo', 'direccion', 'telefono']
from django.shortcuts import render
from dal import autocomplete
from taller.models.documento import Documento
from taller.models.vehiculos import Vehiculo
from taller.models.clientes import Cliente
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        exclude = ['empresa']  # El campo empresa se asigna automáticamente en la vista
from taller.models.tecnico import Tecnico


class DocumentoForm(forms.ModelForm):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.none(),  # Se configura en __init__
        widget=autocomplete.ModelSelect2(
            url='autocomplete-cliente',
            attrs={
                'data-placeholder': '🔍 Buscar cliente...',
                'data-minimum-input-length': 1,
                'class': 'w-full',
            }
        )
    )
    
    vehiculo = forms.ModelChoiceField(
        queryset=Vehiculo.objects.none(),  # Se configura en __init__
        widget=autocomplete.ModelSelect2(
            url='autocomplete-vehiculo',
            forward=['cliente'],
            attrs={
                'data-placeholder': '🔍 Buscar por patente o VIN',
                'data-minimum-input-length': 1,
                'class': 'w-full',
            }
        )
    )
    
    mecanico = forms.CharField(
        label='Mecánico',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Nombre del mecánico'})
    )

    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        if self.empresa:
            self.fields['cliente'].queryset = Cliente.objects.filter(empresa=self.empresa)
            self.fields['vehiculo'].queryset = Vehiculo.objects.filter(empresa=self.empresa)
            
            # Configurar valores por defecto para USA
            if hasattr(self.empresa, 'pais') and self.empresa.pais == 'US':
                self.fields['moneda'].initial = 'USD'
                self.fields['country'].initial = 'US'

    class Meta:
        model = Documento
        fields = ['tipo', 'numero', 'fecha_emision', 'cliente', 'vehiculo', 'estado', 'moneda', 'country']
        widgets = {
            'fecha_emision': forms.DateInput(attrs={'type': 'date'}),
            'tipo': forms.Select(attrs={'class': 'futurista-input'}),
            'estado': forms.Select(attrs={'class': 'futurista-input'}),
            'moneda': forms.Select(attrs={'class': 'futurista-input'}),
            'country': forms.Select(attrs={'class': 'futurista-input'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        mecanico_nombre = self.cleaned_data.get('mecanico')
        if mecanico_nombre:
            mecanico_obj, _ = Tecnico.objects.get_or_create(nombre=mecanico_nombre)
            instance.mecanico = mecanico_obj
        if commit:
            instance.save()
            self.save_m2m()
        return instance

def landing_inicio(request):
    return render(request, "landing_inicio.html")

def contacto_tailwind(request):
    return render(request, "public/contacto_tailwind.html")
