from django import forms
from taller.models.repuesto import Repuesto
from taller.models.tienda import Tienda
from utils.pais import formatear_precio, get_configuracion_pais

class RepuestoForm(forms.ModelForm):
    tienda = forms.ModelChoiceField(
        queryset=Tienda.objects.all(),
        empty_label="-- Seleccionar Tienda --",
        widget=forms.Select(attrs={
            'class': 'input',
            'required': True,
        })
    )
    precio_compra = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'input',
            'id': 'id_precio_compra',
            'inputmode': 'numeric',
            'autocomplete': 'off',
        })
    )
    precio_venta = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'input',
            'id': 'id_precio_venta',
            'inputmode': 'numeric',
            'autocomplete': 'off',
        })
    )

    def __init__(self, *args, **kwargs):
        # Extraer usuario para obtener configuración de país
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Configurar placeholders y formatos según el país
        if self.user and hasattr(self.user, 'empresa'):
            config = get_configuracion_pais(self.user.empresa)
            simbolo = config['simbolo_moneda']
            moneda = config['moneda']
            
            # Actualizar placeholders con la moneda correcta
            self.fields['precio_compra'].widget.attrs.update({
                'placeholder': f'{simbolo}0.00 {moneda}' if config['decimales'] > 0 else f'{simbolo}0 {moneda}'
            })
            self.fields['precio_venta'].widget.attrs.update({
                'placeholder': f'{simbolo}0.00 {moneda}' if config['decimales'] > 0 else f'{simbolo}0 {moneda}'
            })

    class Meta:
        model = Repuesto
        fields = ['tienda', 'nombre_repuesto', 'part_number', 'precio_compra', 'precio_venta', 'stock']
        widgets = {
            'nombre_repuesto': forms.TextInput(attrs={'class': 'input'}),
            'part_number': forms.TextInput(attrs={'class': 'input'}),
            'stock': forms.NumberInput(attrs={'class': 'input'}),
        }

    def clean_precio_compra(self):
        valor = self.cleaned_data['precio_compra']
        # Determinar formato según el país del usuario
        if self.user and hasattr(self.user, 'empresa'):
            config = get_configuracion_pais(self.user.empresa)
            separador_decimal = '.' if config['decimales'] > 0 else ''
        else:
            separador_decimal = '.'  # Default
            
        # Limpiar el valor: eliminar símbolos de moneda y separadores
        limpio = str(valor).replace('$', '').replace('USD', '').replace('CLP', '').strip()
        
        if separador_decimal and '.' in limpio:
            # Para monedas con decimales (USD)
            limpio = limpio.replace(',', '')  # Remover separadores de miles
            try:
                return float(limpio)
            except ValueError:
                raise forms.ValidationError("El precio de compra debe ser un número válido")
        else:
            # Para monedas sin decimales (CLP)
            limpio = limpio.replace('.', '').replace(',', '')  # Remover todos los separadores
            try:
                return int(limpio)
            except ValueError:
                raise forms.ValidationError("El precio de compra debe ser un número válido")

    def clean_precio_venta(self):
        valor = self.cleaned_data['precio_venta']
        # Determinar formato según el país del usuario
        if self.user and hasattr(self.user, 'empresa'):
            config = get_configuracion_pais(self.user.empresa)
            separador_decimal = '.' if config['decimales'] > 0 else ''
        else:
            separador_decimal = '.'  # Default
            
        # Limpiar el valor: eliminar símbolos de moneda y separadores
        limpio = str(valor).replace('$', '').replace('USD', '').replace('CLP', '').strip()
        
        if separador_decimal and '.' in limpio:
            # Para monedas con decimales (USD)
            limpio = limpio.replace(',', '')  # Remover separadores de miles
            try:
                return float(limpio)
            except ValueError:
                raise forms.ValidationError("El precio de venta debe ser un número válido")
        else:
            # Para monedas sin decimales (CLP)
            limpio = limpio.replace('.', '').replace(',', '')  # Remover todos los separadores
            try:
                return int(limpio)
            except ValueError:
                raise forms.ValidationError("El precio de venta debe ser un número válido")

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Los valores ya están limpios por los métodos clean_*
        # No necesitamos hacer nada extra aquí
        if commit:
            instance.save()
        return instance
