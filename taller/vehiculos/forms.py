from datetime import date

from dal import autocomplete

from django import forms

from taller.models import Vehiculo
from taller.models.clientes import Cliente
from taller.models.extras_vehiculo import CajaVehiculo, ColorVehiculo, MotorVehiculo

# Sentinel global para "Agregar nuevo"
NEW_SENTINEL = "__nuevo__"


class VehiculoForm(forms.ModelForm):
    """Formulario para crear y editar vehículos con soporte para USA y Chile"""

    # Año dinámico (current_year + 1 hasta 1970)
    current_year = date.today().year
    anio = forms.TypedChoiceField(
        choices=[(str(y), str(y)) for y in range(current_year + 1, 1969, -1)],
        coerce=int,
        label="Año",
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        assert self.user is not None, "VehiculoForm requiere user=..."

        empresa = getattr(self.user, "empresa", None)
        pais = (getattr(empresa, "pais", None) or "CL").strip().upper()

        # Filtrar clientes por empresa
        if "cliente" in self.fields and empresa:
            self.fields["cliente"].queryset = Cliente.objects.filter(
                empresa=empresa
            ).order_by("nombre", "apellido")

        # Configurar campo color
        self._configurar_color(pais)

        # Etiqueta de año según el país (UX)
        if pais == "US":
            self.fields["anio"].label = "Year"
            self._configurar_campos_usa()
        else:
            self._configurar_campos_chile()

    def _configurar_color(self, pais):
        """Configurar campo color basado en el país y empresa"""
        empresa = getattr(self.user, "empresa", None)
        qs = ColorVehiculo.get_colores_para_pais(pais)
        # Si tu modelo tiene FK a empresa, descomenta:
        # if hasattr(ColorVehiculo, "empresa") and empresa:
        #     qs = qs.filter(empresa=empresa)

        colores_choices = [("", "---------")]
        for color in qs:
            colores_choices.append((str(color.id), color.nombre))
        colores_choices.append(("__nuevo__", "Agregar nuevo color..."))

        self.fields["color"] = forms.ChoiceField(
            choices=colores_choices,
            required=False,
            label="Color",
            widget=forms.Select(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400"
                }
            ),
        )

        if self.instance and getattr(self.instance, "color_id", None):
            self.fields["color"].initial = str(self.instance.color_id)

    def _configurar_campos_usa(self):
        """Configurar campos específicos para usuarios de USA"""
        from taller.models.marca import Marca

        empresa = getattr(self.user, "empresa", None)

        # Campo marca para USA
        marcas_usa = Marca.objects.filter(country="US")
        # Si tu modelo Marca tiene FK empresa, descomenta:
        # if hasattr(Marca, "empresa") and empresa:
        #     marcas_usa = marcas_usa.filter(empresa=empresa)
        marcas_usa = marcas_usa.order_by("nombre")

        self.fields["marca"] = forms.ModelChoiceField(
            queryset=marcas_usa,
            required=True,
            label="Brand",
            empty_label="Select a brand",
            widget=forms.Select(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400"
                }
            ),
        )

        # Campo modelo para USA (se carga dinámicamente via JavaScript)
        # ✅ Usar CharField con widget Select para evitar validación de queryset estático
        self.fields["modelo"] = forms.CharField(
            required=True,
            label="Model",
            widget=forms.Select(
                choices=[("", "Select brand and year first")],
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400"
                },
            ),
        )

        # Campos motor y caja (se cargan dinámicamente via JavaScript)
        # ✅ Usar CharField con widget Select para evitar validación de choices dinámicas
        self.fields["motor"] = forms.CharField(
            required=False,
            label="Engine",
            widget=forms.Select(
                choices=[
                    ("", "Select a model first"),
                    (NEW_SENTINEL, "➕ Add new engine..."),
                ],
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400"
                },
            ),
        )

        self.fields["caja"] = forms.CharField(
            required=False,
            label="Transmission",
            widget=forms.Select(
                choices=[
                    ("", "Select a model first"),
                    (NEW_SENTINEL, "➕ Add new transmission..."),
                ],
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400"
                },
            ),
        )

        # Configurar valores iniciales si estamos editando
        self._configurar_valores_iniciales_usa()

    def _configurar_campos_chile(self):
        """Configurar campos específicos para usuarios de Chile"""
        from taller.models.marca import Marca

        empresa = getattr(self.user, "empresa", None)

        # Campo marca para Chile
        marcas = Marca.objects.filter(country="CL")
        # Si Marca tiene empresa:
        # if hasattr(Marca, "empresa") and empresa:
        #     marcas = marcas.filter(empresa=empresa)
        marcas = marcas.order_by("nombre")

        marcas_choices = [("", "---------")] + [(str(m.pk), m.nombre) for m in marcas]

        self.fields["marca"] = forms.ChoiceField(
            choices=marcas_choices,
            required=True,
            label="Marca",
            widget=forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 rounded-xl bg-black/70 text-cyan-200 font-bold focus:outline-none focus:ring-2 focus:ring-cyan-400"
                }
            ),
        )

        # Campo modelo para Chile
        self.fields["modelo"] = forms.ChoiceField(
            choices=[("", "---------")],
            required=True,
            label="Modelo",
            widget=forms.Select(
                attrs={
                    "class": "w-full px-4 py-2 rounded-xl bg-black/70 text-cyan-200 font-bold focus:outline-none focus:ring-2 focus:ring-cyan-400"
                }
            ),
        )

    def _configurar_valores_iniciales_usa(self):
        """Configurar valores iniciales para usuarios de USA"""
        if self.instance and self.instance.pk:
            # Establecer marca inicial
            if self.instance.marca_id:
                self.fields["marca"].initial = self.instance.marca_id

                # ✅ Cargar modelos de la marca inicial en el widget
                from taller.models.modelo import Modelo

                modelos_iniciales = Modelo.objects.filter(
                    marca_id=self.instance.marca_id, country="US"
                ).order_by("nombre")

                modelos_choices = [("", "Select brand and year first")]
                for modelo in modelos_iniciales:
                    modelos_choices.append((str(modelo.pk), str(modelo)))

                self.fields["modelo"].widget.choices = modelos_choices

                if getattr(self.instance, "modelo_id", None):
                    self.fields["modelo"].initial = str(self.instance.modelo_id)

            # Si hay POST, respeta el modelo enviado
            if self.data and "modelo" in self.data and self.data.get("modelo"):
                self.fields["modelo"].initial = str(self.data.get("modelo"))

            # Cargar motores y cajas del modelo inicial
            modelo_actual = self.instance.modelo

            # Si estamos en POST (con errores), usar el modelo del POST
            if self.data and "modelo" in self.data:
                try:
                    modelo_id_post = self.data.get("modelo")
                    if modelo_id_post:
                        from taller.models.modelo import Modelo

                        modelo_actual = Modelo.objects.get(pk=modelo_id_post)
                except:
                    pass

            if modelo_actual:
                # Cargar motores del modelo
                motores_modelo = MotorVehiculo.objects.filter(
                    modelos=modelo_actual
                ).order_by("nombre")
                motores_choices = [("", "---------")]
                for motor in motores_modelo:
                    motores_choices.append((str(motor.pk), motor.nombre))
                motores_choices.append((NEW_SENTINEL, "➕ Add new engine..."))

                # ✅ Actualizar choices del widget (CharField con widget Select)
                self.fields["motor"].widget.choices = motores_choices

                # Cargar cajas del modelo
                cajas_modelo = CajaVehiculo.objects.filter(
                    modelos=modelo_actual
                ).order_by("nombre")
                cajas_choices = [("", "---------")]
                for caja in cajas_modelo:
                    cajas_choices.append((str(caja.pk), caja.nombre))
                cajas_choices.append((NEW_SENTINEL, "➕ Add new transmission..."))

                # ✅ Actualizar choices del widget (CharField con widget Select)
                self.fields["caja"].widget.choices = cajas_choices

            # Establecer motor inicial
            motor_initial = None
            if self.instance.motor_id:
                motor_initial = str(self.instance.motor_id)
            elif self.data and "motor" in self.data:
                motor_initial = self.data.get("motor")

            if motor_initial:
                self.fields["motor"].initial = motor_initial

            # Establecer caja inicial
            caja_initial = None
            if self.instance.caja_id:
                caja_initial = str(self.instance.caja_id)
            elif self.data and "caja" in self.data:
                caja_initial = self.data.get("caja")

            if caja_initial:
                self.fields["caja"].initial = caja_initial

    def clean(self):
        cleaned_data = super().clean()

        # ✅ NO cortar validaciones cruzadas - ejecutarlas siempre
        # Permite que validaciones de coherencia se ejecuten incluso con errores previos

        empresa = getattr(self.user, "empresa", None)
        pais = (getattr(empresa, "pais", None) or "CL").strip().upper()

        # Validación multi-tenant: Cliente debe pertenecer a la misma empresa
        cliente = cleaned_data.get("cliente")
        if cliente and hasattr(cliente, "empresa_id"):
            if cliente.empresa_id != getattr(empresa, "id", None):
                self.add_error("cliente", "El cliente no pertenece a tu empresa")

        # Validaciones de país para marca y modelo
        marca = cleaned_data.get("marca")
        modelo = cleaned_data.get("modelo")

        # Validar que marca pertenece al país del usuario
        if marca and hasattr(marca, "country"):
            if marca.country != pais:
                self.add_error("marca", "La marca no pertenece a tu país")

        # Validar que modelo pertenece al país del usuario
        if modelo and hasattr(modelo, "country"):
            if modelo.country != pais:
                self.add_error("modelo", "El modelo no pertenece a tu país")

        # Validar coherencia marca-modelo
        if marca and modelo:
            if hasattr(modelo, "marca_id") and hasattr(marca, "id"):
                if modelo.marca_id != marca.id:
                    self.add_error(
                        "modelo", "El modelo no pertenece a la marca seleccionada"
                    )

        # Validaciones básicas de presencia (ambos países)
        if not marca:
            self.add_error("marca", "Debe seleccionar una marca")
        if not modelo:
            self.add_error("modelo", "Debe seleccionar un modelo")

        return cleaned_data

    def clean_marca(self):
        """Convertir ID de marca a instancia (para Chile)"""
        empresa = getattr(self.user, "empresa", None)
        pais = (getattr(empresa, "pais", None) or "CL").strip().upper()
        val = self.cleaned_data.get("marca")

        # En USA, marca ya es instancia (ModelChoiceField)
        if pais != "CL":
            return val

        # En Chile, convertir ID a instancia
        if not val:
            raise forms.ValidationError("Debe seleccionar una marca")

        from taller.models.marca import Marca

        try:
            obj = Marca.objects.get(pk=val, country="CL")
            return obj
        except Marca.DoesNotExist:
            raise forms.ValidationError("Marca no válida para Chile")

    def clean_modelo(self):
        """Convertir ID de modelo a instancia (para USA y Chile)"""
        empresa = getattr(self.user, "empresa", None)
        pais = (getattr(empresa, "pais", None) or "CL").strip().upper()
        val = self.cleaned_data.get("modelo")

        if not val:
            raise forms.ValidationError("Debe seleccionar un modelo")

        from taller.models.modelo import Modelo

        # ✅ Para USA y Chile: convertir ID (string) a instancia
        try:
            # Si val ya es una instancia (edge case), devolverla
            if isinstance(val, Modelo):
                return val

            # Convertir ID a instancia
            modelo_id = int(val)
            obj = Modelo.objects.get(pk=modelo_id, country=pais)

            # Verificar coherencia con la marca elegida
            marca = self.cleaned_data.get("marca")
            if marca:
                # Si marca es instancia, comparar IDs
                marca_id = marca.id if hasattr(marca, "id") else None
                if marca_id and hasattr(obj, "marca_id") and obj.marca_id != marca_id:
                    raise forms.ValidationError(
                        "El modelo no pertenece a la marca seleccionada"
                    )

            return obj
        except (ValueError, TypeError):
            raise forms.ValidationError("ID de modelo no válido")
        except Modelo.DoesNotExist:
            raise forms.ValidationError(f"Modelo no válido para {pais}")

    def clean_color(self):
        """Manejar color con opción de crear nuevo"""
        color_id = self.cleaned_data.get("color")

        if color_id == NEW_SENTINEL:
            self._color_nuevo = True
            return None
        elif color_id:
            try:
                color_obj = ColorVehiculo.objects.get(pk=color_id)
                return color_obj
            except ColorVehiculo.DoesNotExist:
                self.add_error("color", "Color no válido")
                return None
        return None

    def clean_motor(self):
        """Manejar motor con opción de crear nuevo"""
        motor_id = self.cleaned_data.get("motor")

        # Si está vacío o es None, retornar None
        if not motor_id or motor_id == "":
            return None

        if motor_id == NEW_SENTINEL:
            self._motor_nuevo = True
            return None

        # Intentar convertir a entero y buscar el motor
        try:
            motor_obj = MotorVehiculo.objects.get(pk=int(motor_id))
        except (ValueError, TypeError):
            raise forms.ValidationError("ID de motor no válido")
        except MotorVehiculo.DoesNotExist:
            raise forms.ValidationError("Motor no válido")

        # ✅ Verificar pertenencia al modelo seleccionado (si tu relación es M2M 'modelos')
        modelo = self.cleaned_data.get("modelo")
        if modelo and hasattr(motor_obj, "modelos"):
            if not motor_obj.modelos.filter(pk=modelo.pk).exists():
                self.add_error(
                    "motor", "El motor no corresponde al modelo seleccionado"
                )
        return motor_obj

    def clean_caja(self):
        """Manejar caja con opción de crear nuevo"""
        caja_id = self.cleaned_data.get("caja")

        # Si está vacío o es None, retornar None
        if not caja_id or caja_id == "":
            return None

        if caja_id == NEW_SENTINEL:
            self._caja_nuevo = True
            return None

        # Intentar convertir a entero y buscar la caja
        try:
            caja_obj = CajaVehiculo.objects.get(pk=int(caja_id))
        except (ValueError, TypeError):
            raise forms.ValidationError("ID de caja no válido")
        except CajaVehiculo.DoesNotExist:
            raise forms.ValidationError("Caja no válida")

        # ✅ Verificar pertenencia al modelo seleccionado (M2M 'modelos')
        modelo = self.cleaned_data.get("modelo")
        if modelo and hasattr(caja_obj, "modelos"):
            if not caja_obj.modelos.filter(pk=modelo.pk).exists():
                self.add_error("caja", "La caja no corresponde al modelo seleccionado")
        return caja_obj

    def save(self, commit=True):
        """Guardar el vehículo con manejo especial de campos personalizados"""
        vehiculo = super().save(commit=False)
        request = getattr(self, "request", None)
        empresa = getattr(self.user, "empresa", None)
        pais = (getattr(empresa, "pais", None) or "CL").strip().upper()

        modelo = self.cleaned_data.get("modelo")

        # Color
        if (
            getattr(self, "_color_nuevo", False)
            and request
            and request.POST.get("nuevo_color")
        ):
            kwargs = {"nombre": request.POST["nuevo_color"]}
            if hasattr(ColorVehiculo, "country"):
                kwargs["country"] = pais
            if hasattr(ColorVehiculo, "empresa") and empresa:
                kwargs["empresa"] = empresa
            color_obj, _ = ColorVehiculo.objects.get_or_create(**kwargs)
            vehiculo.color = color_obj

        # Motor
        if (
            getattr(self, "_motor_nuevo", False)
            and request
            and request.POST.get("nuevo_motor")
        ):
            kwargs = {"nombre": request.POST["nuevo_motor"]}
            if hasattr(MotorVehiculo, "country"):
                kwargs["country"] = pais
            if hasattr(MotorVehiculo, "empresa") and empresa:
                kwargs["empresa"] = empresa
            motor_obj, _ = MotorVehiculo.objects.get_or_create(**kwargs)
            vehiculo.motor = motor_obj
            if modelo and hasattr(motor_obj, "modelos"):
                motor_obj.modelos.add(modelo)

        # Caja
        if (
            getattr(self, "_caja_nuevo", False)
            and request
            and request.POST.get("nuevo_caja")
        ):
            kwargs = {"nombre": request.POST["nuevo_caja"]}
            if hasattr(CajaVehiculo, "country"):
                kwargs["country"] = pais
            if hasattr(CajaVehiculo, "empresa") and empresa:
                kwargs["empresa"] = empresa
            caja_obj, _ = CajaVehiculo.objects.get_or_create(**kwargs)
            vehiculo.caja = caja_obj
            if modelo and hasattr(caja_obj, "modelos"):
                caja_obj.modelos.add(modelo)

        if commit:
            vehiculo.save()
            self.save_m2m()
        return vehiculo

    class Meta:
        model = Vehiculo
        fields = [
            "cliente",
            "anio",
            "marca",
            "modelo",
            "patente",
            "vin",
            "color",
            "motor",
            "caja",
        ]
        widgets = {
            "cliente": autocomplete.ModelSelect2(
                url="taller:vehiculos:cliente_autocomplete",
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400",
                    "data-placeholder": "Buscar cliente por nombre, email o teléfono...",
                    "data-minimum-input-length": 2,
                    "data-allow-clear": "true",
                },
            ),
            "patente": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400"
                }
            ),
            "vin": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400"
                }
            ),
        }
