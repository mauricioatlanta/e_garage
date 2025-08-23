from dal import autocomplete
from django import forms
from taller.models.vehiculos import Vehiculo
from taller.models.extras_vehiculo import ColorVehiculo, MotorVehiculo, CajaVehiculo
from django.urls import reverse_lazy


class VehiculoForm(forms.ModelForm):

    # Campos personalizados para USA (no ligados al modelo)
    marca_usa = None
    modelo_usa = None

    def add_usa_fields(self):
        """Agregar campos específicos para usuarios de USA"""
        try:
            from taller.models.catalogo import CatalogoModeloAuto
            
            # Verificar que el catálogo esté disponible
            if CatalogoModeloAuto:
                print('DEBUG: Agregando campos USA usando catálogo')
                
                # Obtener marcas del catálogo (get_marcas_activas retorna strings directamente)
                marcas_list = list(CatalogoModeloAuto.get_marcas_activas())
                marcas_choices = [(m, m) for m in marcas_list]
                
                # Campo de marca USA con Select2
                self.fields['marca_usa'] = forms.ChoiceField(
                    choices=[('', 'Select Brand...')] + marcas_choices,
                    required=True,
                    label='Brand (USA)',
                    widget=forms.Select(attrs={
                        'class': 'form-control select2',
                        'id': 'id_marca_usa',
                        'data-placeholder': 'Select brand...',
                        'data-allow-clear': 'true'
                    })
                )
                
                # Campo de modelo USA (se carga dinámicamente via AJAX)
                self.fields['modelo_usa'] = forms.CharField(
                    required=True,
                    label='Model (USA)',
                    widget=forms.Select(attrs={
                        'class': 'form-control select2',
                        'id': 'id_modelo_usa',
                        'data-placeholder': 'First select a brand...',
                        'disabled': 'disabled',
                        'data-allow-clear': 'true'
                    })
                )
                
                print(f'DEBUG: USA fields added - {len(marcas_choices)} marcas disponibles')
            else:
                print('DEBUG: CatalogoModeloAuto no disponible')
                
        except ImportError as e:
            print(f'DEBUG: Error importing CatalogoModeloAuto: {e}')
            # Fallback - podrías implementar campos básicos aquí si es necesario

    # Años 2026 -> 1970 (pedido del usuario) 
    anio = forms.TypedChoiceField(
        choices=[(str(y), str(y)) for y in range(2026, 1969, -1)],
        coerce=int,
        label="Año"
    )


    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        assert self.user is not None, "VehiculoForm requiere user=..."
        empresa = getattr(self.user, 'empresa', None)
        pais = (getattr(empresa, 'pais', None) or 'CL').strip().upper()

        # Modificar el campo color para incluir la opción "Agregar nuevo"
        from taller.models.extras_vehiculo import ColorVehiculo
        colores_choices = [(str(c.id), c.nombre) for c in ColorVehiculo.objects.all()]
        colores_choices.append(('__nuevo__', 'Agregar nuevo color...'))
        
        # Cambiar a ChoiceField para permitir opciones personalizadas
        from django import forms
        self.fields['color'] = forms.ChoiceField(
            choices=[('', '---------')] + colores_choices,
            required=False,
            widget=forms.Select(attrs={
                'class': 'w-full px-4 py-2 rounded-xl bg-black/70 text-cyan-200 font-bold focus:outline-none focus:ring-2 focus:ring-cyan-400'
            })
        )

        if pais == 'US':
            self.add_usa_fields()
            # Campos marca/modelo ya están excluidos del Meta, no necesitamos widgets
        else:
            # Chile: podríamos agregar campos marca/modelo dinámicamente aquí si fuera necesario
            pass

    def clean(self):
        cleaned_data = super().clean()
        if self.user and hasattr(self.user, 'empresa') and self.user.empresa.pais == 'US':
            # Asignar los valores seleccionados en los campos personalizados a los campos reales
            marca_usa = cleaned_data.get('marca_usa')
            modelo_usa = cleaned_data.get('modelo_usa')
            if marca_usa:
                cleaned_data['marca'] = marca_usa
            if modelo_usa:
                cleaned_data['modelo'] = modelo_usa
        return cleaned_data

    def clean_patente(self):
        """Permitir cualquier formato de patente (sin restricción por país)"""
        patente = self.cleaned_data.get('patente', '')
        return patente

    def clean_color(self):
        """Permitir la opción especial '__nuevo__' para agregar un color personalizado"""
        color = self.cleaned_data.get('color')
        
        # Si es la opción especial para agregar nuevo color, validar que se proporcionó el nombre
        if color == '__nuevo__':
            return color  # Permitir esta opción especial
        
        return color

    class Meta:
        model = Vehiculo
        # Excluir 'marca', 'modelo', 'empresa' y 'color' del ModelForm 
        # Se manejan manualmente en la vista para permitir opciones personalizadas
        exclude = ('marca', 'modelo', 'empresa', 'color')
        widgets = {
            'cliente': autocomplete.ModelSelect2(
                url=reverse_lazy('vehiculos:autocomplete_cliente'),
                attrs={
                    'data-placeholder': 'Escribe para buscar o ver sugerencias...',
                    'data-minimum-input-length': 0
                }
            ),
            # Widgets simplificados para motor/caja (evita dependencias DAL en entorno Chile básico)
            'motor': forms.Select(),
            'caja': forms.Select(),
        }
