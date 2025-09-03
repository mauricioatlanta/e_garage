from dal import autocomplete
from django import forms
from taller.models.vehiculos import Vehiculo
from taller.models.extras_vehiculo import ColorVehiculo, MotorVehiculo, CajaVehiculo
from django.urls import reverse_lazy


class VehiculoForm(forms.ModelForm):

    # Años 2026 -> 1970 (pedido del usuario) 
    anio = forms.TypedChoiceField(
        choices=[(str(y), str(y)) for y in range(2026, 1969, -1)],
        coerce=int,
        label="Año"
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.request = kwargs.pop('request', None)  # Extraer request sin pasarlo a super()
        super().__init__(*args, **kwargs)
        assert self.user is not None, "VehiculoForm requiere user=..."
        empresa = getattr(self.user, 'empresa', None)
        pais = (getattr(empresa, 'pais', None) or 'CL').strip().upper()
        
        # DEBUG: Log del país detectado
        print(f'[DEBUG FORM] Usuario: {self.user.username}, Empresa: {getattr(empresa, "id", "None")}, País: {pais}')

        # Configurar campo color como CharField para mayor flexibilidad
        from taller.models.extras_vehiculo import ColorVehiculo
        # Obtener colores disponibles para mostrar como sugerencias
        colores_pais = ColorVehiculo.get_colores_para_pais(pais)
        colores_sugerencias = [c.nombre for c in colores_pais]
        
        # Cambiar a CharField para permitir cualquier color
        from django import forms
        
        # Obtener el valor inicial del color (nombre en lugar de ID)
        color_inicial = ''
        if self.instance and self.instance.color:
            color_inicial = self.instance.color.nombre
        
        self.fields['color'] = forms.CharField(
            required=False,
            label='Color',
            initial=color_inicial,
            widget=forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400',
                'placeholder': f'Color del vehículo (sugerencias: {", ".join(colores_sugerencias[:5])})'
            })
        )

        if pais == 'US':
            # Para usuarios de USA: usar catálogo USA
            print(f'[DEBUG FORM] Configurando campos para USA (pais={pais})')
            try:
                from taller.models.catalogo import CatalogoModeloAuto
                
                if CatalogoModeloAuto:
                    print('[DEBUG FORM] Configurando campos USA usando catálogo')
                    
                    # Obtener marcas del catálogo USA
                    marcas_usa = list(CatalogoModeloAuto.get_marcas_activas())
                    marcas_choices = [('', '---------')] + [(m, m) for m in marcas_usa]
                    print(f'[DEBUG FORM] Configurando {len(marcas_usa)} marcas de USA')
                    
                    # Campo marca_texto para USA (usando catálogo)
                    self.fields['marca_texto'] = forms.ChoiceField(
                        choices=marcas_choices,
                        required=True,
                        label='Brand',
                        widget=forms.Select(attrs={
                            'class': 'w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400'
                        })
                    )
                    
                    # Campo modelo_texto para USA (se carga dinámicamente via AJAX)
                    self.fields['modelo_texto'] = forms.ChoiceField(
                        choices=[('', '---------')],
                        required=True,
                        label='Model',
                        widget=forms.Select(attrs={
                            'class': 'w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400'
                        })
                    )
                    
                    # Configurar campos motor y caja como ChoiceField
                    self.fields['motor'] = forms.ChoiceField(
                        choices=[('', '---------')],
                        required=False,
                        label='Engine',
                        widget=forms.Select(attrs={
                            'class': 'w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400'
                        })
                    )
                    
                    self.fields['caja'] = forms.ChoiceField(
                        choices=[('', '---------')],
                        required=False,
                        label='Transmission',
                        widget=forms.Select(attrs={
                            'class': 'w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400'
                        })
                    )
                    
                    # CLAVE: Configurar dependencia entre marca y modelo para USA
                    marca_inicial = None
                    if self.instance and self.instance.pk and self.instance.marca_texto:
                        marca_inicial = self.instance.marca_texto
                    elif self.instance and self.instance.pk and self.instance.marca:
                        # MIGRACIÓN: Si el vehículo tiene marca antigua (ForeignKey), migrarla a texto
                        marca_inicial = str(self.instance.marca)
                        # Actualizar el campo en la base de datos
                        self.instance.marca_texto = marca_inicial
                        self.instance.save(update_fields=['marca_texto'])
                        print(f'[DEBUG FORM] Migrado marca antigua "{marca_inicial}" a marca_texto')
                    else:
                        marca_inicial = (self.data.get('marca_texto') or None)

                    if marca_inicial:
                        # Para USA, la marca es un string del catálogo
                        try:
                            modelos = CatalogoModeloAuto.get_modelos_por_marca(marca_inicial)
                            modelos_choices = [('', '---------')] + [(m, m) for m in modelos]
                            self.fields['modelo_texto'].choices = modelos_choices
                        except Exception:
                            # Si hay error, dejar opciones vacías
                            pass
                    
                    # CLAVE: Establecer valores iniciales para vehículos existentes
                    if self.instance and self.instance.pk:
                        # Establecer marca inicial
                        if self.instance.marca_texto:
                            self.fields['marca_texto'].initial = self.instance.marca_texto
                        elif self.instance.marca:
                            # MIGRACIÓN: Usar marca antigua como inicial
                            marca_migrada = str(self.instance.marca)
                            self.fields['marca_texto'].initial = marca_migrada
                            print(f'[DEBUG FORM] Usando marca migrada como inicial: {marca_migrada}')
                        
                        # Establecer modelo inicial
                        if self.instance.modelo_texto:
                            self.fields['modelo_texto'].initial = self.instance.modelo_texto
                        elif self.instance.modelo:
                            # MIGRACIÓN: Usar modelo antiguo como inicial
                            modelo_migrado = str(self.instance.modelo)
                            self.fields['modelo_texto'].initial = modelo_migrado
                            # Actualizar el campo en la base de datos
                            self.instance.modelo_texto = modelo_migrado
                            self.instance.save(update_fields=['modelo_texto'])
                            print(f'[DEBUG FORM] Migrado modelo antiguo "{modelo_migrado}" a modelo_texto')
                        
                        # Establecer motor inicial
                        if self.instance.motor_id:
                            self.fields['motor'].initial = str(self.instance.motor_id)
                        
                        # Establecer caja inicial
                        if self.instance.caja_id:
                            self.fields['caja'].initial = str(self.instance.caja_id)
                    
                    # IMPORTANTE: Remover campos de Chile para evitar confusión
                    if 'marca' in self.fields:
                        del self.fields['marca']
                        print('[DEBUG FORM] Campo marca (Chile) removido')
                    if 'modelo' in self.fields:
                        del self.fields['modelo']
                        print('[DEBUG FORM] Campo modelo (Chile) removido')
                    
                else:
                    print('[DEBUG FORM] Catálogo global no disponible')
                    
            except ImportError:
                print('DEBUG: Error importing CatalogoModeloAuto')
                # Fallback si no se puede importar el catálogo
                pass
        else:
            # Chile: agregar campos marca y modelo como ChoiceField
            print(f'[DEBUG FORM] Configurando campos para Chile (pais={pais})')
            from taller.models.marca import Marca
            from taller.models.modelo import Modelo
            
            # Campo marca para Chile
            marcas = Marca.objects.filter(country='CL').order_by('nombre')
            marcas_choices = [('', '---------')] + [(str(m.id), m.nombre) for m in marcas]
            print(f'[DEBUG FORM] Configurando {len(marcas)} marcas de Chile')
            self.fields['marca'] = forms.ChoiceField(
                choices=marcas_choices,
                required=True,
                label='Marca',
                widget=forms.Select(attrs={
                    'class': 'w-full px-4 py-2 rounded-xl bg-black/70 text-cyan-200 font-bold focus:outline-none focus:ring-2 focus:ring-cyan-400'
                })
            )
            
            # Campo modelo para Chile (se carga dinámicamente)
            # IMPORTANTE: Cambiar a ChoiceField para que funcione con dependencias
            self.fields['modelo'] = forms.ChoiceField(
                choices=[('', '---------')],
                required=True,
                label='Modelo',
                widget=forms.Select(attrs={
                    'class': 'w-full px-4 py-2 rounded-xl bg-black/70 text-cyan-200 font-bold focus:outline-none focus:ring-2 focus:ring-cyan-400'
                })
            )
            
            # Configurar campos motor y caja como ChoiceField (se cargan dinámicamente)
            self.fields['motor'] = forms.ChoiceField(
                choices=[('', '---------')],
                required=False,
                label='Motor',
                widget=forms.Select(attrs={
                    'class': 'w-full px-4 py-2 rounded-xl bg-black/70 text-cyan-200 font-bold focus:outline-none focus:ring-2 focus:ring-cyan-400'
                })
            )
            
            # Caja
            self.fields['caja'] = forms.ChoiceField(
                choices=[('', '---------')],
                required=False,
                label='Caja',
                widget=forms.Select(attrs={
                    'class': 'w-full px-4 py-2 rounded-xl bg-black/70 text-cyan-200 font-bold focus:outline-none focus:ring-2 focus:ring-cyan-400'
                })
            )
            
            # CLAVE: Configurar dependencia entre marca y modelo
            # Si estamos editando, precargar el modelo actual
            marca_inicial = None
            if self.instance and self.instance.pk and self.instance.marca_id:
                marca_inicial = self.instance.marca_id
            else:
                # También intenta leer marca desde POST para que al validar no se pierda
                marca_inicial = (self.data.get('marca') or None)

            if marca_inicial:
                # Filtrar modelos por la marca seleccionada
                modelos = Modelo.objects.filter(marca_id=marca_inicial).order_by('nombre')
                modelos_choices = [('', '---------')] + [(str(m.id), m.nombre) for m in modelos]
                self.fields['modelo'].choices = modelos_choices
                
                # Si hay un modelo seleccionado, asegurar que esté en las opciones
                if self.instance and self.instance.modelo_id:
                    modelo_actual = str(self.instance.modelo_id)
                    if not any(choice[0] == modelo_actual for choice in modelos_choices):
                        # Agregar el modelo actual si no está en la lista
                        try:
                            modelo_obj = Modelo.objects.get(id=modelo_actual)
                            self.fields['modelo'].choices.insert(1, (modelo_actual, modelo_obj.nombre))
                        except Modelo.DoesNotExist:
                            pass
                
                # CLAVE: Establecer valores iniciales para vehículos existentes
                if self.instance and self.instance.pk:
                    # Establecer marca inicial
                    if self.instance.marca_id:
                        self.fields['marca'].initial = str(self.instance.marca_id)
                    
                    # Establecer modelo inicial
                    if self.instance.modelo_id:
                        self.fields['modelo'].initial = str(self.instance.modelo_id)
                    
                    # Establecer motor inicial
                    if self.instance.motor_id:
                        self.fields['motor'].initial = str(self.instance.motor_id)
                    
                    # Establecer caja inicial
                    if self.instance.caja_id:
                        self.fields['caja'].initial = str(self.instance.caja_id)

    def add_usa_fields(self):
        """Agregar campos específicos para usuarios de USA"""
        try:
            from taller.models.catalogo import CatalogoModeloAuto
            
            if CatalogoModeloAuto:
                print('DEBUG: Configurando campos USA usando catálogo')
                
                # Obtener marcas del catálogo USA
                marcas_usa = list(CatalogoModeloAuto.get_marcas_activas())
                marcas_choices = [('', '---------')] + [(m, m) for m in marcas_usa]
                
                # Campo marca para USA (usando catálogo)
                self.fields['marca'] = forms.ChoiceField(
                    choices=marcas_choices,
                    required=True,
                    label='Marca',
                    widget=forms.Select(attrs={
                        'class': 'w-full px-4 py-2 rounded-xl bg-black/70 text-cyan-200 font-bold focus:outline-none focus:ring-2 focus:ring-cyan-400'
                    })
                )
                
                # Campo modelo para USA (se carga dinámicamente via AJAX)
                self.fields['modelo'] = forms.ChoiceField(
                    choices=[('', '---------')],
                    required=True,
                    label='Modelo',
                    widget=forms.Select(attrs={
                        'class': 'w-full px-4 py-2 rounded-xl bg-black/70 text-cyan-200 font-bold focus:outline-none focus:ring-2 focus:ring-cyan-400'
                    })
                )
                
                # Configurar campos motor y caja como ChoiceField
                self.fields['motor'] = forms.ChoiceField(
                    choices=[('', '---------')],
                    required=False,
                    label='Motor',
                    widget=forms.Select(attrs={
                        'class': 'w-full px-4 py-2 rounded-xl bg-black/70 text-cyan-200 font-bold focus:outline-none focus:ring-2 focus:ring-cyan-400'
                    })
                )
                
                self.fields['caja'] = forms.ChoiceField(
                    choices=[('', '---------')],
                    required=False,
                    label='Caja',
                    widget=forms.Select(attrs={
                        'class': 'w-full px-4 py-2 rounded-xl bg-black/70 text-cyan-200 font-bold focus:outline-none focus:ring-2 focus:ring-cyan-400'
                    })
                )
                
                print(f'DEBUG: Campos USA configurados - {len(marcas_choices)-1} marcas disponibles')
                
        except ImportError:
            print('DEBUG: Error importing CatalogoModeloAuto')
            # Fallback si no se puede importar el catálogo
            pass

    def clean(self):
        cleaned_data = super().clean()
        if self.user and hasattr(self.user, 'empresa') and self.user.empresa.pais == 'US':
            # Para usuarios de USA, los campos marca y modelo ya están configurados como ChoiceField
            # Solo validar que estén presentes
            marca = cleaned_data.get('marca_texto')
            modelo = cleaned_data.get('modelo_texto')
            
            if not marca:
                self.add_error('marca_texto', 'Debe seleccionar una marca')
            if not modelo:
                self.add_error('modelo_texto', 'Debe seleccionar un modelo')
            
            # Para USA, motor y caja son opcionales
            motor = cleaned_data.get('motor')
            caja = cleaned_data.get('caja')
            
            if motor:
                cleaned_data['motor'] = motor
            else:
                cleaned_data['motor'] = None
                
            if caja:
                cleaned_data['caja'] = caja
            else:
                cleaned_data['caja'] = None
        else:
            # Para Chile, validar que marca y modelo estén presentes y convertirlos a instancias
            marca_id = cleaned_data.get('marca')
            modelo_id = cleaned_data.get('modelo')
            
            if not marca_id:
                self.add_error('marca', 'Debe seleccionar una marca')
            else:
                try:
                    from taller.models.marca import Marca
                    marca = Marca.objects.get(id=marca_id)
                    cleaned_data['marca'] = marca
                except Marca.DoesNotExist:
                    self.add_error('marca', 'Marca no válida')
            
            if not modelo_id:
                self.add_error('modelo', 'Debe seleccionar un modelo')
            else:
                try:
                    from taller.models.modelo import Modelo
                    modelo = Modelo.objects.get(id=modelo_id)
                    cleaned_data['modelo'] = modelo
                except Modelo.DoesNotExist:
                    self.add_error('modelo', 'Modelo no válido')
            
            # Motor y caja son opcionales para Chile
            motor_id = cleaned_data.get('motor')
            caja_id = cleaned_data.get('caja')
            
            if motor_id:
                try:
                    from taller.models.extras_vehiculo import MotorVehiculo
                    motor = MotorVehiculo.objects.get(id=motor_id)
                    cleaned_data['motor'] = motor
                except MotorVehiculo.DoesNotExist:
                    self.add_error('motor', 'Motor no válido')
            else:
                cleaned_data['motor'] = None
                
            if caja_id:
                try:
                    from taller.models.extras_vehiculo import CajaVehiculo
                    caja = CajaVehiculo.objects.get(id=caja_id)
                    cleaned_data['caja'] = caja
                except CajaVehiculo.DoesNotExist:
                    self.add_error('caja', 'Caja no válida')
            else:
                cleaned_data['caja'] = None
            
            # Validar coherencia entre modelo y motor/caja
            modelo = cleaned_data.get('modelo')
            motor = cleaned_data.get('motor')
            caja = cleaned_data.get('caja')
            
            if modelo and motor:
                if not motor.modelos.filter(id=modelo.id).exists():
                    self.add_error('motor', 'Este motor no corresponde al modelo seleccionado.')
            
            if modelo and caja:
                if not caja.modelos.filter(id=modelo.id).exists():
                    self.add_error('caja', 'Esta caja no corresponde al modelo seleccionado.')
        
        return cleaned_data

    def clean_patente(self):
        """Permitir cualquier formato de patente (sin restricción por país)"""
        patente = self.cleaned_data.get('patente', '')
        return patente

    def clean_color(self):
        """Manejar color como texto libre"""
        color = self.cleaned_data.get('color')
        
        if color:
            # Buscar o crear el color
            try:
                from taller.models.extras_vehiculo import ColorVehiculo
                color_obj, created = ColorVehiculo.objects.get_or_create(
                    nombre=color.strip(),
                    defaults={'nombre': color.strip()}
                )
                return color_obj
            except Exception:
                # Si hay error, devolver None (campo opcional)
                return None
        
        return None

    def save(self, commit=True):
        """Guardar el vehículo con manejo especial de campos personalizados"""
        vehiculo = super().save(commit=False)
        
        # El color ya está manejado en clean_color()
        
        if commit:
            vehiculo.save()
            self.save_m2m()
        
        return vehiculo

    class Meta:
        model = Vehiculo
        fields = [
            'cliente', 'anio', 'marca', 'modelo', 'patente', 'vin',
            'color', 'motor', 'caja'
        ]
        widgets = {
            'cliente': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-black border border-cyan-500/30 text-cyan-200 focus:outline-none focus:ring-2 focus:ring-cyan-400/50 focus:border-cyan-400'
            }),
            'anio': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400'
            }),
            'patente': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400'
            }),
            'vin': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400'
            }),
        }
