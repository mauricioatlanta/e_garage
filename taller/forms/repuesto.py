from django import forms
from taller.models.repuesto import Repuesto  # Asegúrate de que este modelo esté bien definido

class RepuestoForm(forms.ModelForm):
    class Meta:
        model = Repuesto
        fields = ['tienda', 'nombre_repuesto', 'part_number', 'precio_compra', 'precio_venta', 'stock']
        widgets = {
            'tienda': forms.Select(attrs={'class': 'input'}),
            'nombre_repuesto': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Nombre del Repuesto'}),
            'part_number': forms.TextInput(attrs={'class': 'input'}),
            'precio_compra': forms.NumberInput(attrs={'class': 'input'}),
            'precio_venta': forms.NumberInput(attrs={'class': 'input'}),
            'stock': forms.NumberInput(attrs={'class': 'input'}),
        }
