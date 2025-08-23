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
from taller.models.tecnico import Tecnico


class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        # Solo lo que el usuario puede editar en DRAFT:
        fields = ["tipo", "cliente", "vehiculo", "moneda", "country", "descuento"]
        widgets = {
            "descuento": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }

    def clean(self):
        cleaned = super().clean()
        if self.instance and self.instance.pk and self.instance.estado != "DRAFT":
            raise forms.ValidationError("No puedes editar un documento emitido/anulado.")
        return cleaned

def landing_inicio(request):
    return render(request, "landing_inicio.html")

def contacto_tailwind(request):
    return render(request, "public/contacto_tailwind.html")
