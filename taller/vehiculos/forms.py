from taller.vehiculos.motor_helper import resolver_o_crear_modelo
from datetime import date

from dal import autocomplete
from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from taller.models import Vehiculo
from taller.models.clientes import Cliente
from taller.models.extras_vehiculo import (
    CajaVehiculo,
    CajaVehiculoEmpresa,
    ColorVehiculo,
    MotorVehiculo,
    MotorVehiculoEmpresa,
)
from taller.vehiculos.catalog_bootstrap import ensure_vehicle_catalog_for_country

# Sentinel global para "Agregar nuevo"
NEW_SENTINEL = "__nuevo__"

# Opciones de tipo de carrocería (traducibles)
CARROCERIA_CHOICES_BASE = [
    ("", "---------"),
    ("sedan", _("Sedan")),
    ("suv", "SUV"),
    ("pickup", _("Pickup")),
    ("hatchback", _("Hatchback")),
    ("coupe", _("Coupe")),
    ("station_wagon", _("Station Wagon")),
    ("van", _("Van")),
    ("minivan", _("Minivan")),
    ("convertible", _("Convertible")),
    ("crossover", _("Crossover")),
    ("compacto", _("Compact")),
    ("utilitario", _("Utility")),
    ("camion", _("Truck")),
    ("otro", _("Other")),
]


class VehiculoForm(forms.ModelForm):
    """Formulario para crear y editar vehículos con soporte para USA y Chile"""

    # Año dinámico (current_year + 1 hasta 1970)
    current_year = date.today().year
    anio = forms.TypedChoiceField(
        choices=[(str(y), str(y)) for y in range(current_year + 1, 1969, -1)],
        coerce=int,
        label="Año",
    )

    # Campo cliente explícitamente definido con autocomplete
    # La URL se configurará dinámicamente en __init__ según el país
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.none(),  # Se configurará en __init__
        widget=autocomplete.ModelSelect2(
            url="chile:vehiculos:cliente_autocomplete",  # Default para Chile, se ajustará en __init__
            attrs={
                "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400",
                "data-placeholder": "Buscar cliente por nombre, email o teléfono...",
                "data-minimum-input-length": 1,
                "data-allow-clear": "true",
            },
        ),
        required=True,
        label="Cliente",
    )

    @staticmethod
    def _resolve_country(user=None, request=None, default="CL"):
        empresa = getattr(user, "empresa", None)
        pais = (getattr(empresa, "pais", None) or default).strip().upper()

        if request:
            path = (request.path or "").lower()
            if path.startswith("/us/"):
                pais = "US"
            elif path.startswith("/cl/"):
                pais = "CL"
            elif path.startswith("/mx/"):
                pais = "MX"

        return pais

    @staticmethod
    def _normalize_free_text_value(raw_value):
        return str(raw_value or "").strip()

    @classmethod
    def _prepare_bound_data(cls, data):
        if not data:
            return data, {}

        mutable_data = data.copy()
        pending = {}

        field_aliases = {
            "motor": ("motor_nuevo", "nuevo_motor"),
            "caja": ("caja_nuevo", "nuevo_caja"),
        }

        for field_name, aliases in field_aliases.items():
            raw_value = cls._normalize_free_text_value(mutable_data.get(field_name))
            extra_value = ""
            for alias in aliases:
                alias_value = cls._normalize_free_text_value(mutable_data.get(alias))
                if alias_value:
                    extra_value = alias_value
                    break

            pending_value = ""
            if raw_value == NEW_SENTINEL:
                pending_value = extra_value
            elif raw_value and not raw_value.isdigit():
                pending_value = raw_value
            elif extra_value:
                pending_value = extra_value

            if not pending_value:
                continue

            pending[field_name] = pending_value
            mutable_data[field_name] = ""
            for alias in aliases:
                mutable_data[alias] = pending_value

        return mutable_data, pending

    class Meta:
        model = Vehiculo
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        # 1. Extraer request y country de forma prioritaria
        self.request = kwargs.pop('request', None) or getattr(self, 'request', None)
        passed_country = kwargs.pop('country', None)
        req_path = ''
        if self.request:
            req_path = getattr(self.request, 'path_info', '') or getattr(self.request, 'path', '') or ''
        
        if '/us/' in req_path.lower() or passed_country in ['US', 'USA']:
            self.country = 'US'
        else:
            self.country = passed_country or getattr(self, 'country', 'CL')
        self.empresa = kwargs.pop('empresa', None) or getattr(self, 'empresa', None)
        self.request = kwargs.pop('request', None) or getattr(self, 'request', None)
        self.empresa = kwargs.pop('empresa', None) or getattr(self, 'empresa', None)
        self.request = kwargs.pop('request', None) or getattr(self, 'request', None)
        self.user = kwargs.pop("user", None)
        args_list = list(args)
        if args_list:
            prepared_data, pending_custom_choices = self._prepare_bound_data(args_list[0])
            args_list[0] = prepared_data
            kwargs.pop('data', None)
        else:
            bound_data = kwargs.get("data")
            prepared_data, pending_custom_choices = self._prepare_bound_data(bound_data)
            if bound_data is not None:
                kwargs["data"] = prepared_data
        super().__init__(*args_list, **kwargs)

        if "empresa" in self.fields:
            self.fields["empresa"].required = False
            if self.empresa:
                self.initial.setdefault("empresa", self.empresa.pk)
        if "tipo_uso" in self.fields:
            self.fields["tipo_uso"].required = False

        # Desactivar validación estricta de ModelChoiceField para campos dinámicos
        for campo_dinamico in ['cliente', 'color', 'motor', 'caja', 'modelo']:
            if campo_dinamico in self.fields:
                self.fields[campo_dinamico].required = False
                # Reemplazar validate por función dummy para aceptar cualquier ID o texto
                self.fields[campo_dinamico].validate = lambda val: None

        assert self.user is not None, "VehiculoForm requiere user=..."

        self._pending_motor_nombre = pending_custom_choices.get("motor", "")
        self._pending_caja_nombre = pending_custom_choices.get("caja", "")
        self._motor_nuevo = bool(self._pending_motor_nombre)
        self._caja_nuevo = bool(self._pending_caja_nombre)

        # The request tenant is authoritative during QA context switching.
        # Keep the owner's company as the fallback for regular requests.
        empresa = getattr(self.request, "empresa", None) or getattr(self.user, "empresa", None)
        if "cliente" in self.fields and isinstance(
            self.fields["cliente"], forms.ModelChoiceField
        ):
            self.fields["cliente"].queryset = Cliente.objects.filter(empresa=empresa)
        # Detectar país: primero de empresa, luego de request.path
        # Detección estricta para entorno USA
        req_path = getattr(self.request, 'path_info', '') or getattr(self.request, 'path', '') or ''
        if '/us/' in req_path.lower() or (getattr(self, 'country', None) and str(self.country).upper() in ['US', 'USA']):
            pais = 'US'
            self.country = 'US'
        else:
            pais = self._resolve_country(self.user, self.request, default="CL")

        if pais == 'US':
            self._configurar_campos_usa()
        else:
            self._configurar_campos_latam(pais=pais)

        # Resolver URL de autocomplete según país
        path_str = req_path.lower()
        if '/us/' in path_str or pais == 'US':
            autocomplete_url = 'us_es:vehiculos:cliente_autocomplete'
        elif '/cl/' in path_str or pais == 'CL':
            autocomplete_url = 'chile:vehiculos:cliente_autocomplete'
        elif '/mx/' in path_str or pais == 'MX':
            autocomplete_url = 'mexico:vehiculos:cliente_autocomplete'
        else:
            autocomplete_url = 'taller:vehiculos:cliente_autocomplete'

            try:
                # No pasar lang como kwarg ya que el URL pattern no lo acepta
                absolute_url = reverse(motor_url_name)

                if lang:
                    # Usar _url directamente para evitar que DAL intente hacer reverse
                    self.fields["motor"].widget._url = absolute_url
                    log.info(
                        f"[VehiculoForm] ✅ URL absoluta configurada para motor (con lang={lang}): {absolute_url}"
                    )
                else:
                    self.fields["motor"].widget._url = motor_url_name
                    log.info(
                        f"[VehiculoForm] ✅ URL de autocomplete motor actualizada: {motor_url_name}"
                    )
            except Exception as e:
                log.warning(
                    f"[VehiculoForm] No se pudo generar URL absoluta para motor: {e}, usando namespace: {motor_url_name}"
                )
                # Intentar usar el namespace directamente (puede fallar si requiere lang)
                try:
                    self.fields["motor"].widget._url = motor_url_name
                except Exception:
                    pass

        # Configurar caja
        # Verificar si el campo existe y si el widget es de tipo autocomplete sin acceder a url
        # Usar isinstance para verificar el tipo sin acceder a propiedades
        if "caja" in self.fields and isinstance(
            self.fields["caja"].widget, autocomplete.ModelSelect2
        ):
            caja_url_name = f"{autocomplete_ns}:caja-autocomplete"
            try:
                # No pasar lang como kwarg ya que el URL pattern no lo acepta
                absolute_url = reverse(caja_url_name)

                if lang:
                    # Usar _url directamente para evitar que DAL intente hacer reverse
                    self.fields["caja"].widget._url = absolute_url
                    log.info(
                        f"[VehiculoForm] ✅ URL absoluta configurada para caja (con lang={lang}): {absolute_url}"
                    )
                else:
                    self.fields["caja"].widget._url = caja_url_name
                    log.info(
                        f"[VehiculoForm] ✅ URL de autocomplete caja actualizada: {caja_url_name}"
                    )
            except Exception as e:
                log.warning(
                    f"[VehiculoForm] No se pudo generar URL absoluta para caja: {e}, usando namespace: {caja_url_name}"
                )
                # Intentar usar el namespace directamente (puede fallar si requiere lang)
                try:
                    self.fields["caja"].widget._url = caja_url_name
                except Exception:
                    pass


        # --- FORZAR OPCIONES DE MOTOR Y CAJA PARA USA ---
        try:
            from taller.models.extras_vehiculo import MotorVehiculo, CajaVehiculo
        except ImportError:
            from taller.models import MotorVehiculo, CajaVehiculo

        es_usa = (getattr(self, 'country', None) == 'US' or 
                  getattr(self, 'pais', None) == 'US' or 
                  (hasattr(self, 'request') and self.request and '/us/' in getattr(self.request, 'path', '')))

        if es_usa:
            if 'motor' in self.fields:
                m_list = list(MotorVehiculo.objects.filter(country='US').order_by('nombre'))
                choices_m = [('', 'Select or type engine...')] + [(str(m.id), m.nombre) for m in m_list]
                self.fields['motor'].choices = choices_m
                self.fields['motor'].widget = forms.Select(
                    choices=choices_m,
                    attrs={
                        'class': 'form-control select2-motor',
                        'id': 'id_motor',
                        'data-placeholder': 'Select or type engine...',
                        'data-tags': 'true'
                    }
                )

            if 'caja' in self.fields:
                c_list = list(CajaVehiculo.objects.filter(country='US').order_by('nombre'))
                choices_c = [('', 'Select or type transmission...')] + [(str(c.id), c.nombre) for c in c_list]
                self.fields['caja'].choices = choices_c
                self.fields['caja'].widget = forms.Select(
                    choices=choices_c,
                    attrs={
                        'class': 'form-control select2-caja',
                        'id': 'id_caja',
                        'data-placeholder': 'Select or type transmission...',
                        'data-tags': 'true'
                    }
                )

    def _configurar_campos_usa(self):
        # Desactivar validación rígida para campos dinámicos en USA
        for fld in ['color', 'motor', 'caja', 'modelo', 'cliente']:
            if fld in self.fields:
                self.fields[fld].required = False
                self.fields[fld].empty_values = [None, '', '---------']
                self.fields[fld].validate = lambda val: None

        # Transformar campos a CharField para admitir texto libre o IDs sin invalid_choice
        from django import forms
        for f_name in ['color', 'motor', 'caja', 'cliente', 'modelo']:
            if f_name in self.fields:
                w = self.fields[f_name].widget
                self.fields[f_name] = forms.CharField(required=False, widget=w)

        if 'color' in self.fields:
            colores = ColorVehiculo.get_colores_para_pais('US')
            opciones_color = [('', 'Select color...')] + [
                (str(color.pk), color.nombre) for color in colores
            ]
            self.fields['color'].widget.choices = opciones_color

        

        # Permitir valores creados al vuelo sin disparar invalid_choice
        for campo_f in ['color', 'motor', 'caja', 'cliente']:
            if campo_f in self.fields:
                self.fields[campo_f].required = False
                self.fields[campo_f].validate = lambda val: None

        # Permitir texto libre sin error de choice inválido
        if 'color' in self.fields:
            self.fields['color'].required = False
            self.fields['color'].empty_values = [None, '', '---------']
        if 'motor' in self.fields:
            self.fields['motor'].required = False
            self.fields['motor'].empty_values = [None, '', '---------']
        if 'caja' in self.fields:
            self.fields['caja'].required = False
            self.fields['caja'].empty_values = [None, '', '---------']

        # Desactivar widget DAL para USA y convertir en ChoiceField estándar con opciones
        try:
            from taller.models.extras_vehiculo import MotorVehiculo, CajaVehiculo
        except ImportError:
            from taller.models import MotorVehiculo, CajaVehiculo

        if 'motor' in self.fields:
            motores_qs = MotorVehiculo.objects.filter(country='US').order_by('nombre')
            opciones_m = [('', 'Select or type engine...')] + [(str(m.id), m.nombre) for m in motores_qs]
            self.fields['motor'].choices = opciones_m
            self.fields['motor'].widget = forms.Select(choices=opciones_m, attrs={
                'class': 'form-control select2-motor',
                'id': 'id_motor',
                'data-placeholder': 'Select or type engine...',
                'data-tags': 'true'
            })

        if 'caja' in self.fields:
            cajas_qs = CajaVehiculo.objects.filter(country='US').order_by('nombre')
            opciones_c = [('', 'Select or type transmission...')] + [(str(c.id), c.nombre) for c in cajas_qs]
            self.fields['caja'].choices = opciones_c
            self.fields['caja'].widget = forms.Select(choices=opciones_c, attrs={
                'class': 'form-control select2-caja',
                'id': 'id_caja',
                'data-placeholder': 'Select or type transmission...',
                'data-tags': 'true'
            })

        """Configurar campos específicos para usuarios de USA"""
        from taller.models.marca import Marca
        import logging

        log = logging.getLogger(__name__)

        empresa = getattr(self.user, "empresa", None)

        # Eliminar el campo marca si ya existe (del Meta) para reemplazarlo
        if "marca" in self.fields:
            log.info("[VehiculoForm._configurar_campos_usa] Eliminando campo marca existente")
            del self.fields["marca"]

        # Campo marca para USA - PRIORIZAR Marca (IDs) sobre Catalogo para que
        # modelos_por_marca_api funcione (requiere marca_id numérico)
        try:
            # 1) Intentar modelo Marca primero (IDs → modelos cargan correctamente)
            marcas_usa = Marca.objects.filter(country="US").order_by("nombre")
            total_marcas = marcas_usa.count()
            log.info(
                f"[VehiculoForm._configurar_campos_usa] Marcas en modelo Marca (country='US'): {total_marcas}"
            )

            if total_marcas > 0:
                marcas_list = list(marcas_usa[:500])
                log.info(
                    f"[VehiculoForm._configurar_campos_usa] Usando modelo Marca ({len(marcas_list)} marcas con IDs)"
                )
                log.info(
                    f"[VehiculoForm._configurar_campos_usa] Primeras 5 marcas: {[m.nombre for m in marcas_list[:5]]}"
                )

                marcas_choices = [("", "Select a brand")]
                for marca in marcas_list:
                    marca_nombre = marca.nombre.strip() if marca.nombre else ""
                    marca_id_str = str(marca.pk).strip()
                    if marca_nombre and marca_id_str and not marca_nombre.isdigit():
                        marcas_choices.append((marca_id_str, marca_nombre))
                    else:
                        log.warning(
                            f"[VehiculoForm._configurar_campos_usa] ⚠️ Marca ID {marca.pk} omitida (nombre inválido)"
                        )

                marcas_choices_tuple = tuple(marcas_choices)
                self.fields["marca"] = forms.ChoiceField(
                    choices=marcas_choices_tuple,
                    required=False,
                    label="Brand",
                    widget=forms.Select(
                        attrs={
                            "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400"
                        }
                    ),
                )
                log.info(
                    f"[VehiculoForm._configurar_campos_usa] ✅ Campo marca con {len(marcas_choices)-1} opciones (IDs)"
                )
            else:
                # Fallback: CatalogoModeloAuto (strings) - modelos no cargarán vía API
                try:
                    from taller.models.catalogo import CatalogoModeloAuto

                    marcas_catalogo = list(CatalogoModeloAuto.get_marcas_activas()[:500])
                except (ImportError, Exception):
                    marcas_catalogo = []
                if marcas_catalogo:
                    log.info(
                        "[VehiculoForm._configurar_campos_usa] Usando catálogo (modelos requerirán agregar manual)"
                    )
                    marcas_choices = [("", "Select a brand")] + [(m, m) for m in marcas_catalogo]
                    self.fields["marca"] = forms.ChoiceField(
                        choices=marcas_choices,
                        required=False,
                        label="Brand",
                        widget=forms.Select(
                            attrs={
                                "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200"
                            }
                        ),
                    )
                else:
                    log.error(
                        "[VehiculoForm._configurar_campos_usa] 💡 Ejecutar: python manage.py cargar_marcas_usa"
                    )
                    self.fields["marca"] = forms.ChoiceField(
                        choices=[("", "No brands - Run: python manage.py cargar_marcas_usa")],
                        required=False,
                        label="Brand",
                        widget=forms.Select(
                            attrs={
                                "class": "w-full px-4 py-3 rounded-lg bg-black border border-red-500/30 text-red-200"
                            }
                        ),
                    )
        except ImportError:
            # Si CatalogoModeloAuto no existe, usar modelo Marca
            log.info(
                "[VehiculoForm._configurar_campos_usa] CatalogoModeloAuto no existe, usando modelo Marca"
            )
            marcas_usa = Marca.objects.filter(country="US").order_by("nombre")
            total_import = marcas_usa.count()
            log.info(
                f"[VehiculoForm._configurar_campos_usa] Marcas en modelo Marca (ImportError): {total_import}"
            )

            if marcas_usa.exists():
                # Convertir a ChoiceField con choices estáticas
                marcas_choices = [("", "Select a brand")]
                for m in marcas_usa:
                    # ✅ VALIDACIÓN: Asegurar que la marca tenga nombre válido y no sea solo un número
                    marca_nombre = m.nombre.strip() if m.nombre else ""
                    marca_id_str = str(m.pk).strip()

                    # Validar que el nombre no sea solo un número (posible error de datos)
                    if marca_nombre and marca_id_str and not marca_nombre.isdigit():
                        marcas_choices.append((marca_id_str, marca_nombre))
                    else:
                        log.warning(
                            f"[VehiculoForm._configurar_campos_usa] ⚠️ Marca con ID {m.pk} tiene nombre inválido '{marca_nombre}', omitiendo"
                        )
                self.fields["marca"] = forms.ChoiceField(
                    choices=marcas_choices,
                    required=False,
                    label="Brand",
                    widget=forms.Select(
                        attrs={
                            "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400"
                        }
                    ),
                )
                log.info(
                    f"[VehiculoForm._configurar_campos_usa] ✅ Campo marca creado como ChoiceField con {len(marcas_choices)-1} marcas"
                )
            else:
                # No hay marcas disponibles
                log.error(
                    "[VehiculoForm._configurar_campos_usa] ❌ No hay marcas disponibles (ImportError fallback)"
                )
                log.error(
                    "[VehiculoForm._configurar_campos_usa] 💡 Ejecutar: python manage.py cargar_marcas_usa"
                )
                self.fields["marca"] = forms.ChoiceField(
                    choices=[("", "No brands available - Run: python manage.py cargar_marcas_usa")],
                    required=False,
                    label="Brand",
                    widget=forms.Select(
                        attrs={
                            "class": "w-full px-4 py-3 rounded-lg bg-black border border-red-500/30 text-red-200 focus:outline-none focus:ring-2 focus:ring-red-400/50 focus:border-red-400"
                        }
                    ),
                )

        # Campo modelo para USA (se carga dinámicamente via JavaScript)
        # ✅ Usar CharField con widget Select para evitar validación de queryset estático
        self.fields["modelo"] = forms.CharField(
            required=False,
            label="Model",
            widget=forms.Select(
                choices=[("", "Select brand and year first")],
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400"
                },
            ),
        )

        # Campos motor y caja con autocomplete y soporte de tags (creación al vuelo)
        from taller.models.extras_vehiculo import CajaVehiculo, MotorVehiculo

        # Detectar país para filtrar queryset
        empresa = getattr(self.user, "empresa", None)
        pais = (getattr(empresa, "pais", None) or "US").strip().upper()
        if self.request:
            path = (self.request.path or "").lower()
            if path.startswith("/us/"):
                pais = "US"
            elif path.startswith("/cl/"):
                pais = "CL"
            elif path.startswith("/mx/"):
                pais = "MX"

        # Determinar namespace correcto para autocomplete según el país
        if self.request:
            path = (self.request.path or "").lower()
            if path.startswith("/us/"):
                autocomplete_ns = "usa:vehiculos"
            elif path.startswith("/cl/"):
                autocomplete_ns = "chile:vehiculos"
            elif path.startswith("/mx/"):
                autocomplete_ns = "mexico:vehiculos"
            else:
                autocomplete_ns = "taller:vehiculos"
        else:
            autocomplete_ns = "taller:vehiculos"

        self.fields["motor"] = forms.CharField(
            required=False,
            label="Engine",
            widget=autocomplete.Select2(
                url=f"{autocomplete_ns}:motor-autocomplete",
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400",
                    "data-placeholder": "Select or type to create new engine...",
                    "data-minimum-input-length": 0,
                    "data-tags": "true",
                },
                forward=["modelo"],
            ),
        )

        self.fields["caja"] = forms.CharField(
            required=False,
            label="Transmission",
            widget=autocomplete.Select2(
                url=f"{autocomplete_ns}:caja-autocomplete",
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400",
                    "data-placeholder": "Select or type to create new transmission...",
                    "data-minimum-input-length": 0,
                    "data-tags": "true",
                },
                forward=["modelo"],
            ),
        )

        self._filtrar_motor_caja_por_modelo(pais)

        # Configurar valores iniciales si estamos editando
        self._configurar_valores_iniciales_usa()

        # ✅ Asegurar que todos los campos básicos tengan sus valores iniciales
        # Esto es necesario porque al reconfigurar campos, Django puede perder los valores iniciales
        if self.instance and self.instance.pk:
            # Restaurar valores iniciales de campos básicos que podrían haberse perdido
            if hasattr(self.instance, "patente"):
                self.fields["patente"].initial = self.instance.patente
            if hasattr(self.instance, "vin"):
                self.fields["vin"].initial = self.instance.vin
            if hasattr(self.instance, "anio") and self.instance.anio:
                self.fields["anio"].initial = str(self.instance.anio)
            if hasattr(self.instance, "millas") and self.instance.millas is not None:
                self.fields["millas"].initial = self.instance.millas
            if hasattr(self.instance, "cliente_id") and self.instance.cliente_id:
                # Para campos con autocomplete, asegurar que el cliente esté en el queryset
                if self.instance.cliente_id not in [c.pk for c in self.fields["cliente"].queryset]:
                    # Agregar el cliente actual al queryset si no está
                    from taller.models.clientes import Cliente

                    cliente_actual = Cliente.objects.filter(pk=self.instance.cliente_id).first()
                    if cliente_actual:
                        self.fields["cliente"].queryset = self.fields[
                            "cliente"
                        ].queryset | Cliente.objects.filter(pk=self.instance.cliente_id)
                self.fields["cliente"].initial = self.instance.cliente_id
            if hasattr(self.instance, "color_id") and self.instance.color_id:
                self.fields["color"].initial = self.instance.color_id


        # Cargar opciones de motor y caja para USA
        try:
            from taller.models.extras_vehiculo import MotorVehiculo, CajaVehiculo
        except ImportError:
            from taller.models import MotorVehiculo, CajaVehiculo

        motores = list(MotorVehiculo.objects.filter(country='US').order_by('nombre').values_list('id', 'nombre'))
        if 'motor' in self.fields:
            self.fields['motor'].choices = [('', 'Select or type engine...')] + [(str(i), n) for i, n in motores]
            self.fields['motor'].widget.attrs.update({'class': 'form-control select2-motor', 'data-placeholder': 'Select or type engine...'})

        cajas = list(CajaVehiculo.objects.filter(country='US').order_by('nombre').values_list('id', 'nombre'))
        if 'caja' in self.fields:
            self.fields['caja'].choices = [('', 'Select or type transmission...')] + [(str(i), n) for i, n in cajas]
            self.fields['caja'].widget.attrs.update({'class': 'form-control select2-caja', 'data-placeholder': 'Select or type transmission...'})

    def _configurar_campos_latam(self, pais):
        """Configurar campos específicos para usuarios de países Latinoamericanos (CL, MX, etc.)"""
        from taller.models.marca import Marca

        empresa = getattr(self.user, "empresa", None)
        ensure_vehicle_catalog_for_country(pais)
        self.fields["color"].queryset = ColorVehiculo.get_colores_para_pais(pais)

        # Eliminar el campo marca si ya existe (del Meta) para reemplazarlo
        if "marca" in self.fields:
            del self.fields["marca"]

        # Campo marca por país
        marcas = Marca.objects.filter(country=pais)
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

        # Campo modelo para país (se carga dinámicamente via JavaScript)
        # ✅ Usar CharField con widget Select para evitar validación de queryset estático
        self.fields["modelo"] = forms.CharField(
            required=True,
            label="Modelo",
            widget=forms.Select(
                choices=[("", "Selecciona marca y año primero")],
                attrs={
                    "class": "w-full px-4 py-2 rounded-xl bg-black/70 text-cyan-200 font-bold focus:outline-none focus:ring-2 focus:ring-cyan-400"
                },
            ),
        )

        # Campos motor y caja con autocomplete y soporte de tags (creación al vuelo)
        from taller.models.extras_vehiculo import CajaVehiculo, MotorVehiculo

        # Determinar namespace correcto para autocomplete según el país
        if self.request:
            path = (self.request.path or "").lower()
            if path.startswith("/us/"):
                autocomplete_ns = "usa:vehiculos"
            elif path.startswith("/cl/"):
                autocomplete_ns = "chile:vehiculos"
            elif path.startswith("/mx/"):
                autocomplete_ns = "mexico:vehiculos"
            else:
                autocomplete_ns = "taller:vehiculos"
        else:
            autocomplete_ns = "taller:vehiculos"

        self.fields["motor"] = forms.CharField(
            required=False,
            label="Motor",
            widget=autocomplete.Select2(
                url=f"{autocomplete_ns}:motor-autocomplete",
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400",
                    "data-placeholder": "Selecciona o escribe para crear nuevo motor...",
                    "data-minimum-input-length": 0,
                    "data-tags": "true",
                },
                forward=["modelo"],
            ),
        )

        self.fields["caja"] = forms.CharField(
            required=False,
            label="Transmisión",
            widget=autocomplete.Select2(
                url=f"{autocomplete_ns}:caja-autocomplete",
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400",
                    "data-placeholder": "Selecciona o escribe para crear nueva transmisión...",
                    "data-minimum-input-length": 0,
                    "data-tags": "true",
                },
                forward=["modelo"],
            ),
        )

        self._filtrar_motor_caja_por_modelo(pais)

    def _filtrar_motor_caja_por_modelo(self, pais):
        """Filtra querysets de motor y caja por modelo (creación y edición). No depende de self.instance.pk."""
        from taller.models.extras_vehiculo import CajaVehiculo, MotorVehiculo
        from taller.models.modelo import Modelo

        modelo_actual = None
        if self.data and self.data.get("modelo"):
            try:
                modelo_actual = Modelo.objects.get(pk=self.data.get("modelo"), country=pais)
            except Exception:
                modelo_actual = None
        elif self.instance and self.instance.pk and getattr(self.instance, "modelo_id", None):
            modelo_actual = self.instance.modelo

        if "motor" not in self.fields or "caja" not in self.fields:
            return

        if modelo_actual:
            self.fields["motor"].queryset = (
                MotorVehiculo.objects.filter(country=pais, modelos=modelo_actual)
                .distinct()
                .order_by("nombre")
            )
            self.fields["caja"].queryset = (
                CajaVehiculo.objects.filter(country=pais, modelos=modelo_actual)
                .distinct()
                .order_by("nombre")
            )
            if self.instance and self.instance.pk:
                if self.instance.motor_id:
                    self.fields["motor"].queryset = (
                        MotorVehiculo.objects.filter(
                            Q(country=pais, modelos=modelo_actual) | Q(pk=self.instance.motor_id)
                        )
                        .distinct()
                        .order_by("nombre")
                    )
                if self.instance.caja_id:
                    self.fields["caja"].queryset = (
                        CajaVehiculo.objects.filter(
                            Q(country=pais, modelos=modelo_actual) | Q(pk=self.instance.caja_id)
                        )
                        .distinct()
                        .order_by("nombre")
                    )
        else:
            if self.instance and self.instance.pk:
                if self.instance.motor_id:
                    self.fields["motor"].queryset = MotorVehiculo.objects.filter(
                        pk=self.instance.motor_id
                    )
                else:
                    self.fields["motor"].queryset = MotorVehiculo.objects.filter(
                        country=pais
                    ).none()
                if self.instance.caja_id:
                    self.fields["caja"].queryset = CajaVehiculo.objects.filter(
                        pk=self.instance.caja_id
                    )
                else:
                    self.fields["caja"].queryset = CajaVehiculo.objects.filter(country=pais).none()
            else:
                self.fields["motor"].queryset = MotorVehiculo.objects.filter(country=pais).none()
                self.fields["caja"].queryset = CajaVehiculo.objects.filter(country=pais).none()

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

            # Establecer motor inicial
            motor_initial = None
            if getattr(self.instance, "motor_empresa_id", None):
                motor_initial = f"empresa:{self.instance.motor_empresa_id}"
            elif self.instance.motor_id:
                motor_initial = str(self.instance.motor_id)
            elif self.data and "motor" in self.data:
                motor_initial = self.data.get("motor")

            if motor_initial:
                self.fields["motor"].initial = motor_initial

            # Establecer caja inicial
            caja_initial = None
            if getattr(self.instance, "caja_empresa_id", None):
                caja_initial = f"empresa:{self.instance.caja_empresa_id}"
            elif self.instance.caja_id:
                caja_initial = str(self.instance.caja_id)
            elif self.data and "caja" in self.data:
                caja_initial = self.data.get("caja")

            if caja_initial:
                self.fields["caja"].initial = caja_initial


    

    





    def clean_marca(self):
        val = self.cleaned_data.get('marca') or self.data.get('marca')
        if not val or str(val).strip() in ['', 'None', 'null', '---------']:
            return None
        if hasattr(val, 'pk'):
            return val
        from taller.models import Marca
        val_str = str(val).strip()
        if val_str.isdigit():
            obj = Marca.objects.filter(id=int(val_str)).first()
            if obj:
                return obj
        return Marca.objects.filter(nombre__iexact=val_str).first()



    def clean_tipo_uso(self):
        val = self.cleaned_data.get('tipo_uso') or self.data.get('tipo_uso') or 'CLIENTE'
        val_str = str(val).strip()
        if 'tipo_uso' in self.fields and hasattr(self.fields['tipo_uso'], 'choices'):
            choices = dict(self.fields['tipo_uso'].choices)
            if val_str in choices:
                return val_str
            if val_str.upper() in choices:
                return val_str.upper()
            if val_str.lower() in choices:
                return val_str.lower()
            return list(choices.keys())[0] if choices else val_str
        return val_str




    def save(self, commit=True):
        instance = super().save(commit=False)
        
        motor_res = self.cleaned_data.get('motor') or self.clean_motor()
        if motor_res and hasattr(motor_res, 'pk'):
            instance.motor = motor_res
        elif motor_res is None:
            instance.motor = None

        caja_res = self.cleaned_data.get('caja') or self.clean_caja()
        if caja_res and hasattr(caja_res, 'pk'):
            instance.caja = caja_res
        elif caja_res is None:
            instance.caja = None

        modelo_res = self.cleaned_data.get('modelo')
        if modelo_res and hasattr(modelo_res, 'pk'):
            if motor_res and hasattr(motor_res, 'modelos'):
                motor_res.modelos.add(modelo_res)
            if caja_res and hasattr(caja_res, 'modelos'):
                caja_res.modelos.add(modelo_res)

        if commit:
            instance.save()
            self.save_m2m()
        return instance



    def clean_motor(self):
        val = (
            self.data.get('motor')
            or self.cleaned_data.get('motor')
            or self._pending_motor_nombre
        )
        if not val or str(val).strip() in ['', 'None', 'null', '---------']:
            return None
        if hasattr(val, 'pk'):
            return val
        try:
            from taller.models.extras_vehiculo import MotorVehiculo
        except ImportError:
            from taller.models import MotorVehiculo

        val_str = str(val).strip()
        if val_str.isdigit():
            obj = MotorVehiculo.objects.filter(id=int(val_str)).first()
            if obj:
                return obj
        country = getattr(self, 'country', None) or 'US'
        obj = MotorVehiculo.objects.filter(nombre__iexact=val_str, country=country).first()
        if not obj:
            obj = MotorVehiculo.objects.create(nombre=val_str, country=country)
        return obj

    def clean_caja(self):
        val = (
            self.data.get('caja')
            or self.cleaned_data.get('caja')
            or self._pending_caja_nombre
        )
        if not val or str(val).strip() in ['', 'None', 'null', '---------']:
            return None
        if hasattr(val, 'pk'):
            return val
        try:
            from taller.models.extras_vehiculo import CajaVehiculo
        except ImportError:
            try:
                from taller.models import CajaVehiculo
            except ImportError:
                from taller.models import Transmision as CajaVehiculo

        val_str = str(val).strip()
        if val_str.isdigit():
            obj = CajaVehiculo.objects.filter(id=int(val_str)).first()
            if obj:
                return obj
        country = getattr(self, 'country', None) or 'US'
        obj = CajaVehiculo.objects.filter(nombre__iexact=val_str, country=country).first()
        if not obj:
            obj = CajaVehiculo.objects.create(nombre=val_str, country=country)
        return obj

    def clean_color(self):
        val = self.data.get('color') or self.cleaned_data.get('color')
        if not val or str(val).strip() in ['', 'None', 'null', '---------']:
            return None
        if hasattr(val, 'pk'):
            return val
        try:
            from taller.models.extras_vehiculo import ColorVehiculo
        except ImportError:
            from taller.models import ColorVehiculo
        val_str = str(val).strip()
        if val_str.isdigit():
            obj = ColorVehiculo.objects.filter(id=int(val_str)).first()
            if obj:
                return obj
        obj = ColorVehiculo.objects.filter(nombre__iexact=val_str).first()
        if not obj:
            country = getattr(self, 'country', None) or 'US'
            kwargs = {'nombre': val_str}
            if hasattr(ColorVehiculo, 'country'):
                kwargs['country'] = country
            obj = ColorVehiculo.objects.create(**kwargs)
        return obj

    def clean_modelo(self):
        val = self.data.get('modelo') or self.cleaned_data.get('modelo')
        if not val or str(val).strip() in ['', 'None', 'null', '---------']:
            return None
        if hasattr(val, 'pk'):
            return val
        from taller.models import Modelo, Marca
        val_str = str(val).strip()
        es_nombre_catalogo = val_str.startswith("nombre:")
        if es_nombre_catalogo:
            val_str = val_str.removeprefix("nombre:").strip()
        if val_str.isdigit() and not es_nombre_catalogo:
            m = Modelo.objects.filter(id=int(val_str)).first()
            if m:
                return m
        marca_obj = self.cleaned_data.get('marca')
        if not marca_obj or not hasattr(marca_obj, 'pk'):
            raw_marca = self.data.get('marca')
            if raw_marca and str(raw_marca).isdigit():
                marca_obj = Marca.objects.filter(id=int(raw_marca)).first()
        qs = Modelo.objects.filter(nombre__iexact=val_str)
        if marca_obj:
            qs = qs.filter(marca=marca_obj)
        m = qs.first()
        if not m and marca_obj:
            country = getattr(self, 'country', None) or 'US'
            m = Modelo.objects.create(marca=marca_obj, nombre=val_str, country=country)
        return m

    def clean_cliente(self):
        val = self.data.get('cliente') or self.cleaned_data.get('cliente')
        if not val or str(val).strip() in ['', 'None', 'null', '---------']:
            return None
        if hasattr(val, 'pk'):
            return val
        from taller.models import Cliente
        val_str = str(val).strip()
        if val_str.isdigit():
            c = Cliente.objects.filter(id=int(val_str)).first()
            if c:
                return c
        empresa = getattr(self, 'empresa', None)
        qs = Cliente.objects.all()
        if empresa:
            qs = qs.filter(empresa=empresa)
        return qs.first()

    def clean(self):
        cleaned_data = super().clean()
        
        # Asignar cliente por defecto de la empresa si no viene
        if not cleaned_data.get('cliente'):
            from taller.models import Cliente
            empresa = getattr(self, 'empresa', None)
            c = Cliente.objects.filter(empresa=empresa).first() if empresa else Cliente.objects.first()
            if c:
                cleaned_data['cliente'] = c

        # Mapeo seguro de tipo_uso
        tipo_uso = cleaned_data.get('tipo_uso') or self.data.get('tipo_uso')
        if not tipo_uso:
            cleaned_data['tipo_uso'] = 'CLIENTE'
            
        return cleaned_data
