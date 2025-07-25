from django import forms
from taller.models.comprobante_pago import ComprobantePago


class ComprobantePagoForm(forms.ModelForm):
    """Formulario para subir comprobantes de pago"""
    
    class Meta:
        model = ComprobantePago
        fields = [
            'metodo_pago', 'monto', 'plan_solicitado', 'comprobante',
            'numero_transaccion', 'descripcion'
        ]
        
        widgets = {
            'metodo_pago': forms.Select(attrs={
                'class': 'form-select',
            }),
            'monto': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 25000',
                'min': '1000',
                'step': '1000',
            }),
            'plan_solicitado': forms.Select(attrs={
                'class': 'form-select',
            }),
            'comprobante': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png',
            }),
            'numero_transaccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de transferencia o transacción',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Información adicional (opcional)',
            }),
        }
        
        labels = {
            'metodo_pago': 'Método de Pago',
            'monto': 'Monto Pagado (CLP)',
            'plan_solicitado': 'Plan Solicitado',
            'comprobante': 'Comprobante de Pago',
            'numero_transaccion': 'Número de Transacción',
            'descripcion': 'Comentarios',
        }
        
        help_texts = {
            'comprobante': 'Sube tu comprobante en formato PDF, JPG o PNG (máximo 5MB)',
            'numero_transaccion': 'Número de referencia de la transferencia o depósito',
            'monto': 'Monto total pagado en pesos chilenos',
        }
    
    def clean_comprobante(self):
        """Validar tamaño y tipo de archivo"""
        archivo = self.cleaned_data.get('comprobante')
        
        if archivo:
            # Validar tamaño (5MB máximo)
            if archivo.size > 5 * 1024 * 1024:
                raise forms.ValidationError('El archivo no puede ser mayor a 5MB')
            
            # Validar extensión
            valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
            ext = archivo.name.lower().split('.')[-1]
            if f'.{ext}' not in valid_extensions:
                raise forms.ValidationError('Solo se permiten archivos PDF, JPG, JPEG o PNG')
        
        return archivo
    
    def clean_monto(self):
        """Validar que el monto sea razonable"""
        monto = self.cleaned_data.get('monto')
        
        if monto and monto < 1000:
            raise forms.ValidationError('El monto mínimo es $1.000')
        if monto and monto > 1000000:
            raise forms.ValidationError('El monto máximo es $1.000.000')
            
        return monto
