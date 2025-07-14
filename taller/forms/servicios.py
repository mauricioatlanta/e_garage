from django import forms
from taller.servicios.models import CategoriaServicio, SubcategoriaServicio, Servicio



class CategoriaServicioForm(forms.ModelForm):
    class Meta:
        model = CategoriaServicio
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
        }



class SubcategoriaServicioForm(forms.ModelForm):
    class Meta:
        model = SubcategoriaServicio
        fields = ['nombre', 'categoria']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
        }



class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['nombre', 'subcategoria']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'subcategoria': forms.Select(attrs={'class': 'form-control'}),
        }
