from django import forms
from django.shortcuts import render
from dal import autocomplete
from taller.models.documento import Documento
from taller.models.vehiculos import Vehiculo
from taller.models.clientes import Cliente
from taller.models.mecanico import Mecanico


class DocumentoForm(forms.ModelForm):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='autocomplete_cliente',
            attrs={'data-placeholder': 'Buscar cliente...'}
        )
    )
    vehiculo = forms.ModelChoiceField(
        queryset=Vehiculo.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='autocomplete_vehiculo',
            forward=['cliente'],
            attrs={'data-placeholder': 'Filtrar vehículo por cliente'}
        )
    )
    mecanico = forms.CharField(
        label='Mecánico',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Nombre del mecánico'})
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
            # 'mecanico',  # No incluir aquí, lo manejamos manualmente
        ]
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        mecanico_nombre = self.cleaned_data.get('mecanico')
        if mecanico_nombre:
            mecanico_obj, _ = Mecanico.objects.get_or_create(nombre=mecanico_nombre)
            instance.mecanico = mecanico_obj
        if commit:
            instance.save()
            self.save_m2m()
        return instance

def landing_inicio(request):
    return render(request, "landing_inicio.html")

def contacto_tailwind(request):
    return render(request, "public/contacto_tailwind.html")
