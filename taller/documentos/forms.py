from django import forms
from .models import Documento
from .lineas_documento import LineaDocumento
from taller.models.tecnico import Tecnico
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo

class DocumentoForm(forms.ModelForm):
    # Campo personalizado para millas/kilometraje del vehículo
    kilometraje = forms.CharField(
        label="Kilometraje/Millas",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input input-number',
            'type': 'number',
            'step': '1',
            'min': '0',
            'placeholder': '0'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        self.user = kwargs.pop('user', None)  # Agregar soporte para user
        super().__init__(*args, **kwargs)
        
        # Configurar widgets con clases CSS
        widget_attrs = {'class': 'form-control'}
        for field_name, field in self.fields.items():
            if field_name not in ['pagado']:  # Excepto campos que ya tienen widgets específicos
                if hasattr(field.widget, 'attrs'):
                    field.widget.attrs.update(widget_attrs)
        
        # Inicializar campo kilometraje con valor del vehículo
        if self.instance and self.instance.vehiculo and self.instance.vehiculo.millas:
            self.fields['kilometraje'].initial = self.instance.vehiculo.millas
        
        # Configurar queryset de técnicos incluyendo el actual
        # Usar la empresa pasada por parámetro o la del documento
        empresa = self.empresa or (self.instance.empresa if self.instance and self.instance.empresa_id else None)
        if self.user and hasattr(self.user, 'empresa'):
            empresa = empresa or self.user.empresa
        
        if empresa:
            # Configurar querysets por empresa para evitar "Select a valid choice"
            # Cliente queryset
            cliente_qs = Cliente.objects.filter(empresa=empresa)
            if self.instance and self.instance.cliente_id:
                cliente_qs = cliente_qs | Cliente.objects.filter(pk=self.instance.cliente_id)
            self.fields["cliente"].queryset = cliente_qs.distinct().order_by("nombre")
            
            # Vehículo queryset  
            vehiculo_qs = Vehiculo.objects.filter(cliente__empresa=empresa)
            if self.instance and self.instance.vehiculo_id:
                vehiculo_qs = vehiculo_qs | Vehiculo.objects.filter(pk=self.instance.vehiculo_id)
            self.fields["vehiculo"].queryset = vehiculo_qs.distinct().order_by("patente")
            
            # Técnico queryset (ya existía)
            qs = Tecnico.objects.filter(empresa=empresa)
            if self.instance and self.instance.tecnico_responsable_id:
                # incluir el técnico actual aunque esté inactivo o filtrado
                qs = qs | Tecnico.objects.filter(pk=self.instance.tecnico_responsable_id)
                self.fields["tecnico_responsable"].initial = self.instance.tecnico_responsable_id
            self.fields["tecnico_responsable"].queryset = qs.distinct().order_by("nombre")
        else:
            # Si no hay empresa, usar querysets vacíos
            self.fields["cliente"].queryset = Cliente.objects.none()
            self.fields["vehiculo"].queryset = Vehiculo.objects.none()
            self.fields["tecnico_responsable"].queryset = Tecnico.objects.none()
        
        # Inicializar el campo UI desde el vehículo
        v = getattr(self.instance, "vehiculo", None)
        if v:
            if hasattr(v, "millas") and v.millas is not None:
                self.fields["kilometraje"].initial = v.millas
            elif hasattr(v, "kilometraje") and v.kilometraje is not None:
                self.fields["kilometraje"].initial = v.kilometraje
    
    def clean_kilometraje(self):
        """Validación personalizada para el campo kilometraje"""
        valor = self.cleaned_data.get('kilometraje')
        if valor:
            valor = valor.strip()
            if valor:
                try:
                    valor = int(valor)
                    if valor < 0:
                        raise forms.ValidationError("El kilometraje no puede ser negativo")
                    if valor > 9999999:
                        raise forms.ValidationError("El kilometraje no puede ser mayor a 9,999,999")
                    return valor
                except (ValueError, TypeError):
                    raise forms.ValidationError("Ingrese un número válido")
        return None
    
    def _norm_decimal(self, s):
        """Normalizar string a decimal (maneja comas, puntos, espacios)"""
        if s is None: 
            return None
        s = str(s).strip().replace(" ", "")
        # Si tiene tanto coma como punto, asumir que coma es separador de miles
        if s.count(",") and s.count("."):
            s = s.replace(".", "").replace(",", ".")
        elif s.count(",") == 1 and not s.count("."):
            # Solo una coma, probablemente separador decimal
            s = s.replace(",", ".")
        return s
    
    def clean(self):
        """Validación general del formulario con normalizacion de decimales"""
        cleaned = super().clean()
        
        # Normalizar campos decimales si vienen del POST
        for k in ("sales_tax_rate",):
            if k in self.data:
                try:
                    normalized = self._norm_decimal(self.data.get(k))
                    if normalized:
                        cleaned[k] = normalized
                except (ValueError, TypeError):
                    pass  # Dejar que la validación normal maneje el error
        
        return cleaned
    
    def save(self, commit=True):
        instance = super().save(commit=commit)
        
        # Persistir millas/kilometraje en el vehículo
        v = getattr(instance, "vehiculo", None)
        kilometraje_valor = self.cleaned_data.get("kilometraje")
        
        if v and kilometraje_valor is not None:
            try:
                if isinstance(kilometraje_valor, str):
                    val = int(kilometraje_valor.strip()) if kilometraje_valor.strip() else None
                else:
                    val = int(kilometraje_valor)
                    
                if val is not None:
                    if hasattr(v, "millas"):
                        v.millas = val
                        if commit:
                            v.save(update_fields=["millas"])
                    elif hasattr(v, "kilometraje"):
                        v.kilometraje = val  
                        if commit:
                            v.save(update_fields=["kilometraje"])
            except (ValueError, TypeError) as e:
                # Manejar errores de conversión de tipo
                print(f"Error al guardar kilometraje: {e}")
        
        return instance
    
    class Meta:
        model = Documento
        fields = ["tipo", "numero", "fecha_emision", "cliente", "vehiculo", "tecnico_responsable", "kilometraje", "moneda", "country", "descuento", "estado_pago", "pagado", "millas", "observaciones"]
        widgets = {
            'tecnico_responsable': forms.Select(attrs={'class': 'form-select'}),
            'estado_pago': forms.Select(attrs={'class': 'form-select'}),
            'pagado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'millas': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Observaciones opcionales - Puede dejarse vacío si no hay información adicional...'
            })
        }

class LineaDocumentoForm(forms.ModelForm):
    class Meta:
        model = LineaDocumento
        fields = ["item_type", "descripcion", "qty", "unit_price"]
