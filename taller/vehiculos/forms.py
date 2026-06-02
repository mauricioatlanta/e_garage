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

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.request = kwargs.pop("request", None)
        args_list = list(args)
        bound_data = kwargs.pop("data", None)
        if args_list:
            bound_data = args_list.pop(0)

        prepared_data, pending_custom_choices = self._prepare_bound_data(bound_data)
        if prepared_data is not None:
            kwargs["data"] = prepared_data

        super().__init__(*args_list, **kwargs)
        assert self.user is not None, "VehiculoForm requiere user=..."

        self._pending_motor_nombre = pending_custom_choices.get("motor", "")
        self._pending_caja_nombre = pending_custom_choices.get("caja", "")
        self._motor_nuevo = bool(self._pending_motor_nombre)
        self._caja_nuevo = bool(self._pending_caja_nombre)

        empresa = getattr(self.user, "empresa", None)
        # Detectar país: primero de empresa, luego de request.path
        pais = self._resolve_country(self.user, self.request, default="CL")

        # Si tenemos request, usar detección robusta del path
        if self.request:
            path = (self.request.path or "").lower()
            if path.startswith("/us/"):
                pais = "US"
            elif path.startswith("/cl/"):
                pais = "CL"
            elif path.startswith("/mx/"):
                pais = "MX"

        # Filtrar clientes por empresa
        if "cliente" in self.fields:
            if empresa:
                self.fields["cliente"].queryset = Cliente.objects.filter(empresa=empresa).order_by(
                    "nombre", "apellido"
                )
            else:
                # Si no hay empresa, usar queryset vacío (el autocomplete lo manejará)
                self.fields["cliente"].queryset = Cliente.objects.none()

            if hasattr(self.fields["cliente"].widget, "attrs"):
                self.fields["cliente"].widget.attrs["data-placeholder"] = (
                    "Buscar cliente por nombre, email o telefono..."
                )

            # Asegurar que el widget tenga la URL correcta del autocomplete según el país
            # Si tenemos request, ajustar la URL según el namespace del país
            if self.request and hasattr(self.fields["cliente"].widget, "url"):
                path = (self.request.path or "").lower()
                import logging
                from django.urls import reverse

                log = logging.getLogger(__name__)

                # Determinar el namespace correcto según el país y ruta
                if path.startswith("/us/es/"):
                    autocomplete_url = "us_es:vehiculos:cliente_autocomplete"
                elif path.startswith("/us/en/"):
                    autocomplete_url = "us_en:vehiculos:cliente_autocomplete"
                elif path.startswith("/us/"):
                    autocomplete_url = "usa:vehiculos:cliente_autocomplete"
                    log.info(
                        f"[VehiculoForm] Configurando URL de autocomplete cliente para USA: {autocomplete_url}"
                    )
                elif path.startswith("/cl/"):
                    # Para Chile, usar el namespace chile:vehiculos:cliente_autocomplete
                    autocomplete_url = "chile:vehiculos:cliente_autocomplete"
                    log.info(
                        f"[VehiculoForm] Configurando URL de autocomplete cliente para Chile: {autocomplete_url}"
                    )
                elif path.startswith("/mx/"):
                    # Para México, usar el namespace mexico:vehiculos:cliente_autocomplete
                    autocomplete_url = "mexico:vehiculos:cliente_autocomplete"
                    log.info(
                        f"[VehiculoForm] Configurando URL de autocomplete cliente para México: {autocomplete_url}"
                    )
                else:
                    # Fallback: usar el namespace genérico
                    autocomplete_url = "taller:vehiculos:cliente_autocomplete"
                    log.warning(
                        f"[VehiculoForm] No se pudo detectar país desde path '{path}', usando namespace genérico: {autocomplete_url}"
                    )

                # Actualizar la URL del widget
                try:
                    # Extraer lang del path si está presente (ej: /us/en/... o /us/es/...)
                    lang = None
                    path_parts = path.strip("/").split("/")
                    if len(path_parts) >= 2 and path_parts[1] in ["en", "es"]:
                        lang = path_parts[1]

                    # Intentar generar la URL absoluta con reverse para asegurar que tenga el prefijo correcto
                    try:
                        # No pasar lang como kwarg ya que el URL pattern no lo acepta
                        # El reverse usará automáticamente el namespace correcto basado en el contexto
                        from django.urls import NoReverseMatch

                        try:
                            absolute_url = reverse(autocomplete_url)
                            log.info(f"[VehiculoForm] URL generada por reverse: {absolute_url}")

                            # Verificar si la URL tiene el prefijo correcto
                            if path.startswith("/us/es/"):
                                expected_prefix = "/us/es/"
                            elif path.startswith("/us/en/"):
                                expected_prefix = "/us/en/"
                            elif path.startswith("/us/"):
                                expected_prefix = "/us/"
                            elif path.startswith("/cl/"):
                                expected_prefix = "/cl/"
                            else:
                                expected_prefix = None

                            if expected_prefix and not absolute_url.startswith(expected_prefix):
                                # Si falta el prefijo, agregarlo
                                if absolute_url.startswith("/"):
                                    absolute_url = expected_prefix.rstrip("/") + absolute_url
                                else:
                                    absolute_url = expected_prefix.rstrip("/") + "/" + absolute_url
                                log.info(
                                    f"[VehiculoForm] Prefijo agregado, URL corregida: {absolute_url}"
                                )

                            # Usar la URL absoluta en el atributo data-ajax--url como fallback
                            if hasattr(self.fields["cliente"].widget, "attrs"):
                                self.fields["cliente"].widget.attrs["data-ajax--url"] = absolute_url
                                log.info(
                                    f"[VehiculoForm] ✅ URL absoluta configurada en data-ajax--url: {absolute_url}"
                                )

                            # Si tenemos lang, usar la URL absoluta directamente en widget.url
                            # para evitar que DAL intente hacer reverse sin el parámetro lang
                            if lang:
                                self.fields["cliente"].widget.url = absolute_url
                                log.info(
                                    f"[VehiculoForm] ✅ URL absoluta configurada en widget.url (con lang={lang}): {absolute_url}"
                                )
                            else:
                                # Sin lang, usar el namespace normal
                                self.fields["cliente"].widget.url = autocomplete_url
                                log.info(
                                    f"[VehiculoForm] ✅ URL de autocomplete cliente actualizada: {autocomplete_url}"
                                )
                        except NoReverseMatch as e:
                            log.warning(
                                f"[VehiculoForm] NoReverseMatch al generar URL: {e}, usando namespace directamente: {autocomplete_url}"
                            )
                            # Si falla el reverse, usar el namespace directamente
                            self.fields["cliente"].widget.url = autocomplete_url
                    except Exception as reverse_error:
                        log.error(
                            f"[VehiculoForm] Error inesperado al generar URL: {reverse_error}, usando namespace: {autocomplete_url}"
                        )
                        # Si falla el reverse, usar el namespace (puede fallar si requiere lang)
                        self.fields["cliente"].widget.url = autocomplete_url
                        log.info(
                            f"[VehiculoForm] ✅ URL de autocomplete cliente actualizada (fallback): {autocomplete_url}"
                        )
                except Exception as e:
                    log.error(f"[VehiculoForm] ❌ Error al actualizar URL de autocomplete: {e}")

        # Configurar campo color
        self._configurar_color(pais)

        # Configurar tipo de carrocería (lista + opción agregar)
        self._configurar_tipo_carroceria(pais)

        # Debug: Log del país detectado
        import logging

        log = logging.getLogger(__name__)
        log.info(
            f"[VehiculoForm] País detectado: {pais} (path: {getattr(self.request, 'path', 'N/A') if self.request else 'N/A'})"
        )

        # Etiqueta de año según el país (UX)
        if pais == "US":
            self.fields["anio"].label = "Year"
            if "millas" in self.fields:
                self.fields["millas"].widget.attrs["placeholder"] = "Miles"
            log.info("[VehiculoForm] Configurando campos USA")
            self._configurar_campos_usa()
        else:
            log.info(f"[VehiculoForm] Configurando campos LATAM para país: {pais}")
            self._configurar_campos_latam(pais)
            if "modelo" in self.fields:
                self.fields["modelo"].widget.choices = [("", "Selecciona marca y ano primero")]
            if "motor" in self.fields:
                self.fields["motor"].widget.attrs["data-placeholder"] = (
                    "Selecciona o escribe para crear un motor nuevo..."
                )
            if "caja" in self.fields:
                self.fields["caja"].label = "Transmision"
                self.fields["caja"].widget.attrs["data-placeholder"] = (
                    "Selecciona o escribe para crear una transmision nueva..."
                )
            if "millas" in self.fields:
                self.fields["millas"].widget.attrs["placeholder"] = "Kilometraje"

        # Configurar URLs de autocomplete para motor y caja si existen
        self._configurar_urls_autocomplete_motor_caja()

        # Debug: verificar que el campo marca se haya creado correctamente
        if "marca" in self.fields:
            marca_field = self.fields["marca"]
            if isinstance(marca_field, forms.ChoiceField):
                choices_count = len(marca_field.choices)
                log.info(
                    f"[VehiculoForm] ✅ Campo marca creado como ChoiceField con {choices_count} opciones (país: {pais})"
                )
                if choices_count > 1:
                    log.info(f"[VehiculoForm] Primeras 5 opciones: {list(marca_field.choices[:5])}")
            elif isinstance(marca_field, forms.ModelChoiceField):
                queryset_count = marca_field.queryset.count()
                log.info(
                    f"[VehiculoForm] ✅ Campo marca creado como ModelChoiceField con {queryset_count} marcas en queryset (país: {pais})"
                )
                if queryset_count > 0:
                    log.info(
                        f"[VehiculoForm] Primeras 5 marcas: {[str(m) for m in marca_field.queryset[:5]]}"
                    )
        else:
            log.warning(
                f"[VehiculoForm] ❌ Campo marca NO encontrado después de configuración (país: {pais})"
            )

        # Flujo "crear vehículo desde documento": si viene next en GET/POST, permitir guardar sin marca/modelo
        # para que el redirect con cliente_id y vehiculo_id funcione; el usuario puede editar después.
        if self.request and (
            self.request.GET.get("return_to")
            or self.request.POST.get("return_to")
            or self.request.GET.get("next")
            or self.request.POST.get("next")
        ):
            if "marca" in self.fields:
                self.fields["marca"].required = False
            if "modelo" in self.fields:
                self.fields["modelo"].required = False
            log.info("[VehiculoForm] Flujo desde documento (next): marca y modelo no requeridos")

        self.pending_motor_nombre = self._pending_motor_nombre
        self.pending_caja_nombre = self._pending_caja_nombre
        self._apply_pending_tag_attrs()

    def _apply_pending_tag_attrs(self):
        pending_map = {
            "motor": getattr(self, "_pending_motor_nombre", ""),
            "caja": getattr(self, "_pending_caja_nombre", ""),
        }

        for field_name, pending_value in pending_map.items():
            field = self.fields.get(field_name)
            if not field or not hasattr(field.widget, "attrs"):
                continue
            if pending_value:
                field.widget.attrs["data-pending-free-text"] = pending_value
            else:
                field.widget.attrs.pop("data-pending-free-text", None)

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
        colores_choices.append(("__nuevo__", _("Agregar nuevo color...")))

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

    def _configurar_tipo_carroceria(self, pais):
        """Configurar campo tipo_carroceria con lista de opciones + agregar nuevo"""
        choices = list(CARROCERIA_CHOICES_BASE) + [("__nuevo__", _("Add new body type..."))]
        label = "Body Type / Style" if pais == "US" else _("Tipo de carrocería / Estilo")
        self.fields["tipo_carroceria"] = forms.ChoiceField(
            choices=choices,
            required=False,
            label=label,
            widget=forms.Select(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400"
                }
            ),
        )
        if self.instance and getattr(self.instance, "tipo_carroceria", None):
            val = (self.instance.tipo_carroceria or "").strip()
            if val and val not in [c[0] for c in choices]:
                # Valor existente no está en la lista (ej. custom) → agregar como opción
                self.fields["tipo_carroceria"].choices = (
                    list(choices[:-1]) + [(val, val)] + [choices[-1]]
                )
            self.fields["tipo_carroceria"].initial = val or ""

    def _configurar_urls_autocomplete_motor_caja(self):
        """Configurar URLs de autocomplete para motor y caja con soporte para lang"""
        import logging
        from django.urls import reverse

        log = logging.getLogger(__name__)

        if not self.request:
            return

        path = (self.request.path or "").lower()

        # Extraer lang del path si está presente (ej: /us/en/... o /us/es/...)
        lang = None
        path_parts = path.strip("/").split("/")
        if len(path_parts) >= 2 and path_parts[1] in ["en", "es"]:
            lang = path_parts[1]

        # Determinar namespace base según el país
        if path.startswith("/us/"):
            autocomplete_ns = "usa:vehiculos"
        elif path.startswith("/cl/"):
            autocomplete_ns = "chile:vehiculos"
        elif path.startswith("/mx/"):
            autocomplete_ns = "mexico:vehiculos"
        else:
            autocomplete_ns = "taller:vehiculos"

        # Configurar motor
        # Verificar si el campo existe y si el widget es de tipo autocomplete sin acceder a url
        # Usar isinstance para verificar el tipo sin acceder a propiedades
        if "motor" in self.fields and isinstance(
            self.fields["motor"].widget, autocomplete.ModelSelect2
        ):
            motor_url_name = f"{autocomplete_ns}:motor-autocomplete"
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

    def _configurar_campos_usa(self):
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
                    required=True,
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
                        required=True,
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
                        required=True,
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
                    required=True,
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
                    required=True,
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
            required=True,
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

    def _configurar_campos_latam(self, pais):
        """Configurar campos específicos para usuarios de países Latinoamericanos (CL, MX, etc.)"""
        from taller.models.marca import Marca

        empresa = getattr(self.user, "empresa", None)
        ensure_vehicle_catalog_for_country(pais)

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

    def clean(self):
        cleaned_data = super().clean()

        # ✅ NO cortar validaciones cruzadas - ejecutarlas siempre
        # Permite que validaciones de coherencia se ejecuten incluso con errores previos

        empresa = getattr(self.user, "empresa", None)
        # Detectar país: primero de empresa, luego de request.path
        pais = self._resolve_country(self.user, self.request, default="CL")

        # Si tenemos request, usar detección robusta del path
        if self.request:
            path = (self.request.path or "").lower()
            if path.startswith("/us/"):
                pais = "US"
            elif path.startswith("/cl/"):
                pais = "CL"
            elif path.startswith("/mx/"):
                pais = "MX"

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
        # ✅ IMPORTANTE: Esta validación se ejecuta DESPUÉS de clean_marca() y clean_modelo()
        # Por lo tanto, marca y modelo ya deberían ser instancias
        if marca and modelo:
            # Asegurar que ambos son instancias de los modelos correctos
            from taller.models.marca import Marca
            from taller.models.modelo import Modelo

            import logging

            log = logging.getLogger(__name__)

            # Verificar que son instancias correctas
            if isinstance(marca, Marca) and isinstance(modelo, Modelo):
                # ✅ CRÍTICO: Recargar modelo con select_related para asegurar que la marca esté cargada
                modelo_fresh = Modelo.objects.select_related("marca").get(pk=modelo.pk)

                marca_id = marca.id
                modelo_marca_id = modelo_fresh.marca_id

                # ✅ CRÍTICO: Convertir a enteros para comparación segura
                try:
                    marca_id_int = int(marca_id)
                    modelo_marca_id_int = int(modelo_marca_id)
                except (ValueError, TypeError) as e:
                    log.error(
                        f"[clean] Error al convertir IDs a enteros: {e}, marca_id={marca_id} (tipo: {type(marca_id)}), modelo_marca_id={modelo_marca_id} (tipo: {type(modelo_marca_id)})"
                    )
                    marca_id_int = marca_id
                    modelo_marca_id_int = modelo_marca_id

                log.info(
                    f"[clean] Validando coherencia: marca.id={marca_id_int} (tipo: {type(marca_id_int)}), "
                    f"modelo.marca_id={modelo_marca_id_int} (tipo: {type(modelo_marca_id_int)}), "
                    f"marca='{marca.nombre}', modelo='{modelo_fresh.nombre}'"
                )

                # ✅ CRÍTICO: Comparar usando == para verificar coherencia
                if modelo_marca_id_int == marca_id_int:
                    log.info(
                        f"[clean] ✅ Coherencia verificada: modelo '{modelo_fresh.nombre}' (ID={modelo_fresh.pk}, marca_id={modelo_marca_id_int}) "
                        f"pertenece a marca '{marca.nombre}' (ID={marca_id_int})"
                    )
                    # NO hacer nada más, la validación pasó correctamente
                else:
                    # Solo si NO coinciden, mostrar error con diagnóstico detallado
                    try:
                        marca_real_del_modelo = modelo_fresh.marca
                        log.error(
                            f"[clean] ❌ Error de coherencia marca-modelo:\n"
                            f"   - Marca seleccionada: ID={marca_id_int} (tipo: {type(marca_id_int)}), Nombre='{marca.nombre}', Country='{marca.country}'\n"
                            f"   - Modelo seleccionado: ID={modelo_fresh.pk}, Nombre='{modelo_fresh.nombre}', Country='{modelo_fresh.country}'\n"
                            f"   - Modelo.marca_id={modelo_marca_id_int} (tipo: {type(modelo_marca_id_int)})\n"
                            f"   - Marca real del modelo: ID={marca_real_del_modelo.id}, Nombre='{marca_real_del_modelo.nombre}', Country='{marca_real_del_modelo.country}'\n"
                            f"   - Comparación: {modelo_marca_id_int} != {marca_id_int}"
                        )

                        # ✅ VERIFICAR EN BD DIRECTAMENTE UNA VEZ MÁS
                        modelo_verificacion_final = Modelo.objects.select_related("marca").get(
                            pk=modelo_fresh.pk
                        )
                        log.error(
                            f"[clean] Verificación final BD: modelo.marca_id={modelo_verificacion_final.marca_id}, "
                            f"marca.id={marca_id_int}, ¿coinciden? {modelo_verificacion_final.marca_id == marca_id_int}"
                        )

                        # ✅ ÚLTIMA VERIFICACIÓN: Comparar directamente sin conversión
                        if modelo_verificacion_final.marca_id == marca_id_int:
                            log.error(
                                f"[clean] ⚠️ ¡INCONSISTENCIA! La comparación directa dice que SÍ coinciden, "
                                f"pero la comparación con int() dice que NO. Esto es un bug."
                            )
                            # NO lanzar error si la comparación directa dice que coinciden
                            return cleaned_data
                    except Exception as e:
                        log.error(f"[clean] Error al obtener marca del modelo: {e}")
                        import traceback

                        log.error(traceback.format_exc())

                    self.add_error(
                        "modelo",
                        f"El modelo '{modelo_fresh.nombre}' no pertenece a la marca '{marca.nombre}' seleccionada. "
                        f"Por favor, seleccione el modelo correcto para esta marca.",
                    )
            elif not isinstance(marca, Marca):
                log.warning(f"[clean] Marca no es instancia de Marca: {type(marca)}, valor={marca}")
            elif not isinstance(modelo, Modelo):
                log.warning(
                    f"[clean] Modelo no es instancia de Modelo: {type(modelo)}, valor={modelo}"
                )

        # Validaciones básicas de presencia (ambos países)
        if not marca:
            self.add_error("marca", "Debe seleccionar una marca")
        if not modelo:
            self.add_error("modelo", "Debe seleccionar un modelo")

        return cleaned_data

    def clean_marca(self):
        """Convertir ID/nombre de marca a instancia"""
        empresa = getattr(self.user, "empresa", None)
        # Detectar país: primero de empresa, luego de request.path
        pais = (getattr(empresa, "pais", None) or "CL").strip().upper()

        # Si tenemos request, usar detección robusta del path
        if self.request:
            path = (self.request.path or "").lower()
            if path.startswith("/us/"):
                pais = "US"
            elif path.startswith("/cl/"):
                pais = "CL"
            elif path.startswith("/mx/"):
                pais = "MX"

        val = self.cleaned_data.get("marca")

        # Flujo desde documento (next): permitir guardar sin marca
        if (
            not val
            and self.request
            and (
                self.request.GET.get("return_to")
                or self.request.POST.get("return_to")
                or self.request.GET.get("next")
                or self.request.POST.get("next")
            )
        ):
            return None
        if not val:
            raise forms.ValidationError("Debe seleccionar una marca")

        from taller.models.marca import Marca

        # En USA, puede ser ID de marca (número) o nombre de marca (del catálogo)
        if pais == "US":
            # Si ya es instancia (ModelChoiceField), retornarla
            if isinstance(val, Marca):
                return val

            # Intentar primero como ID numérico (caso más común)
            if isinstance(val, str):
                try:
                    marca_id = int(val)
                    # Es un ID numérico, obtener la marca por ID
                    try:
                        marca_obj = Marca.objects.get(pk=marca_id, country="US")
                        return marca_obj
                    except Marca.DoesNotExist:
                        raise forms.ValidationError(
                            f"Marca con ID {marca_id} no encontrada para USA"
                        )
                except (ValueError, TypeError):
                    # No es un número, tratar como nombre de marca del catálogo
                    marca_obj, _ = Marca.objects.get_or_create(
                        nombre=val, country="US", defaults={"nombre": val}
                    )
                    return marca_obj
            elif isinstance(val, int):
                # Es un entero directamente
                try:
                    marca_obj = Marca.objects.get(pk=val, country="US")
                    return marca_obj
                except Marca.DoesNotExist:
                    raise forms.ValidationError(f"Marca con ID {val} no encontrada para USA")

            # Fallback: tratar como string
            marca_obj, _ = Marca.objects.get_or_create(
                nombre=str(val), country="US", defaults={"nombre": str(val)}
            )
            return marca_obj

        # En Chile/México, convertir ID a instancia
        try:
            # Intentar como ID primero
            if isinstance(val, str):
                try:
                    marca_id = int(val)
                    obj = Marca.objects.get(pk=marca_id, country=pais)
                    return obj
                except (ValueError, TypeError):
                    pass
            elif isinstance(val, int):
                obj = Marca.objects.get(pk=val, country=pais)
                return obj

            # Si no es un ID, intentar como nombre
            obj = Marca.objects.get(nombre=val, country=pais)
            return obj
        except Marca.DoesNotExist:
            raise forms.ValidationError(f"Marca no válida para {pais}")

    def clean_modelo(self):
        """Convertir ID de modelo a instancia (para USA y Chile)"""
        empresa = getattr(self.user, "empresa", None)
        pais = (getattr(empresa, "pais", None) or "CL").strip().upper()

        # Si tenemos request, usar detección robusta del path
        if self.request:
            path = (self.request.path or "").lower()
            if path.startswith("/us/"):
                pais = "US"
            elif path.startswith("/cl/"):
                pais = "CL"
            elif path.startswith("/mx/"):
                pais = "MX"

        val = self.cleaned_data.get("modelo")

        # Flujo desde documento (next): permitir guardar sin modelo
        if (
            not val
            and self.request
            and (
                self.request.GET.get("return_to")
                or self.request.POST.get("return_to")
                or self.request.GET.get("next")
                or self.request.POST.get("next")
            )
        ):
            return None
        if not val:
            raise forms.ValidationError("Debe seleccionar un modelo")

        from taller.models.modelo import Modelo
        import logging

        log = logging.getLogger(__name__)

        # ✅ Para USA y Chile: convertir ID (string) a instancia
        try:
            # Si val ya es una instancia (edge case), devolverla
            if isinstance(val, Modelo):
                return val

            # Convertir ID a instancia
            modelo_id = int(val)

            # ✅ Obtener modelo con select_related para optimizar y asegurar relación
            try:
                obj = Modelo.objects.select_related("marca").get(pk=modelo_id, country=pais)
            except Modelo.DoesNotExist:
                log.error(
                    f"[clean_modelo] Modelo con ID {modelo_id} no encontrado para país {pais}"
                )
                raise forms.ValidationError(f"Modelo con ID {modelo_id} no válido para {pais}")

            # Verificar coherencia con la marca elegida
            # ✅ CRÍTICO: clean_marca() se ejecuta ANTES que clean_modelo()
            # Por lo tanto, marca DEBERÍA estar en cleaned_data como instancia
            marca = self.cleaned_data.get("marca")

            # ✅ Si marca no está en cleaned_data o no es una instancia, obtenerla del POST
            if not marca or not isinstance(marca, Marca):
                log.warning(
                    f"[clean_modelo] ⚠️ Marca no está en cleaned_data como instancia. "
                    f"Tipo: {type(marca)}, Valor: {marca}"
                )

                if self.data:
                    marca_raw = self.data.get("marca")
                    if marca_raw:
                        try:
                            from taller.models.marca import Marca

                            marca_id_from_post = int(marca_raw)
                            marca = Marca.objects.filter(
                                pk=marca_id_from_post, country=pais
                            ).first()
                            if marca:
                                log.info(
                                    f"[clean_modelo] ✅ Marca obtenida del POST: {marca.nombre} (ID={marca.id}), "
                                    f"country={marca.country}"
                                )
                                # ✅ CRÍTICO: Guardar en cleaned_data como instancia
                                self.cleaned_data["marca"] = marca
                            else:
                                log.error(
                                    f"[clean_modelo] ❌ Marca con ID {marca_id_from_post} no encontrada para país {pais}"
                                )
                        except (ValueError, TypeError) as e:
                            log.error(
                                f"[clean_modelo] ❌ Error al obtener marca del POST: {e}, valor={marca_raw}"
                            )
                else:
                    log.error(f"[clean_modelo] ❌ No hay data disponible para obtener marca")

            # ✅ Si tenemos marca como instancia, validar coherencia
            if marca and isinstance(marca, Marca):
                # Si marca es instancia, comparar IDs
                marca_id = marca.id if hasattr(marca, "id") else None
                if marca_id and hasattr(obj, "marca_id"):
                    # ✅ Obtener marca del modelo usando select_related (ya cargado)
                    modelo_marca_id = obj.marca_id
                    modelo_marca = obj.marca  # Ya está cargado por select_related

                    # ✅ CRÍTICO: Verificar que ambos IDs sean enteros y compararlos correctamente
                    try:
                        marca_id_int = int(marca_id)
                        modelo_marca_id_int = int(modelo_marca_id)
                    except (ValueError, TypeError) as e:
                        log.error(
                            f"[clean_modelo] Error al convertir IDs a enteros: {e}, marca_id={marca_id}, modelo_marca_id={modelo_marca_id}"
                        )
                        raise forms.ValidationError(
                            "Error interno al validar marca y modelo. Por favor, intente nuevamente."
                        )

                    log.info(
                        f"[clean_modelo] Comparando: marca.id={marca_id_int} vs modelo.marca_id={modelo_marca_id_int} "
                        f"(marca: {marca.nombre}, modelo: {obj.nombre})"
                    )

                    # ✅ CRÍTICO: Verificar coherencia pero NO lanzar error aquí
                    # La validación final se hará en clean() después de que ambos campos estén procesados
                    if modelo_marca_id_int == marca_id_int:
                        log.info(
                            f"[clean_modelo] ✅ Coherencia verificada: modelo '{obj.nombre}' (ID={obj.pk}, marca_id={modelo_marca_id_int}) "
                            f"pertenece a marca '{marca.nombre}' (ID={marca_id_int})"
                        )
                        # NO hacer nada más, la validación pasó
                    else:
                        # ✅ DIAGNÓSTICO DETALLADO: Log información completa para debugging
                        log.error(
                            f"[clean_modelo] ❌ Error de coherencia marca-modelo:\n"
                            f"   - Marca seleccionada: ID={marca_id_int} (tipo: {type(marca_id_int)}), Nombre='{marca.nombre}', Country='{getattr(marca, 'country', 'N/A')}'\n"
                            f"   - Modelo seleccionado: ID={obj.pk}, Nombre='{obj.nombre}', Country='{obj.country}'\n"
                            f"   - Modelo.marca_id={modelo_marca_id_int} (tipo: {type(modelo_marca_id_int)})\n"
                            f"   - Marca real del modelo: ID={modelo_marca.id}, Nombre='{modelo_marca.nombre}', Country='{modelo_marca.country}'\n"
                            f"   - Comparación: {modelo_marca_id_int} != {marca_id_int}"
                        )

                        # ✅ VERIFICAR EN BD DIRECTAMENTE
                        modelo_verificacion = Modelo.objects.select_related("marca").get(pk=obj.pk)
                        log.error(
                            f"[clean_modelo] Verificación directa BD: modelo.marca_id={modelo_verificacion.marca_id}, "
                            f"marca.id={marca_id_int}, ¿coinciden? {modelo_verificacion.marca_id == marca_id_int}"
                        )

                        # ✅ NO LANZAR ERROR AQUÍ - Dejar que clean() lo haga después de procesar ambos campos
                        # Esto evita problemas de orden de ejecución
                        log.warning(
                            f"[clean_modelo] ⚠️ Coherencia fallida, pero NO lanzando error aquí. "
                            f"La validación final se hará en clean()"
                        )

                        # ✅ VERIFICAR SI HAY MÚLTIPLES MODELOS CON EL MISMO NOMBRE
                        modelos_mismo_nombre = Modelo.objects.filter(
                            nombre=obj.nombre, country=pais
                        ).select_related("marca")

                        if modelos_mismo_nombre.count() > 1:
                            log.warning(
                                f"[clean_modelo] ⚠️ Hay {modelos_mismo_nombre.count()} modelos con nombre '{obj.nombre}' para país {pais}:"
                            )
                            for m in modelos_mismo_nombre:
                                log.warning(
                                    f"   - ID={m.pk}, Marca='{m.marca.nombre}' (ID={m.marca.id})"
                                )

                        raise forms.ValidationError(
                            f"El modelo '{obj.nombre}' no pertenece a la marca '{marca.nombre}' seleccionada. "
                            f"El modelo pertenece a la marca '{modelo_marca.nombre}'. "
                            f"Por favor, seleccione el modelo correcto para la marca '{marca.nombre}'."
                        )
            else:
                log.warning(
                    f"[clean_modelo] ⚠️ No se pudo obtener marca para validación. "
                    f"La validación se realizará en clean()"
                )

            return obj
        except (ValueError, TypeError) as e:
            log.error(f"[clean_modelo] Error al convertir ID de modelo: {e}, valor recibido: {val}")
            raise forms.ValidationError("ID de modelo no válido")
        except Modelo.DoesNotExist:
            log.error(f"[clean_modelo] Modelo con ID {val} no encontrado para país {pais}")
            raise forms.ValidationError(f"Modelo no válido para {pais}")

    def clean_tipo_carroceria(self):
        """Manejar tipo_carroceria con opción de agregar nuevo"""
        val = self.cleaned_data.get("tipo_carroceria")
        if val == NEW_SENTINEL:
            self._tipo_carroceria_nuevo = True
            return ""
        return val or ""

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
        """Aceptar motores globales o privados con prefijo empresa:<id>."""
        raw_value = (self.cleaned_data.get("motor") or "").strip()
        empresa = getattr(self.user, "empresa", None)
        pais = self._resolve_country(self.user, self.request, default="CL")
        modelo = self.cleaned_data.get("modelo")

        if not raw_value:
            self._motor_empresa_obj = None
            return None

        if raw_value.startswith("empresa:"):
            if not empresa or not modelo:
                raise forms.ValidationError("Motor privado no válido para esta empresa/modelo")
            private_id = raw_value.split(":", 1)[1]
            try:
                motor_privado = MotorVehiculoEmpresa.objects.get(
                    pk=private_id,
                    empresa=empresa,
                    modelo=modelo,
                    country=pais,
                )
            except (MotorVehiculoEmpresa.DoesNotExist, ValueError):
                raise forms.ValidationError("Motor privado no válido")
            self._motor_empresa_obj = motor_privado
            return None

        motor_id = raw_value.split(":", 1)[1] if raw_value.startswith("global:") else raw_value
        try:
            motor = MotorVehiculo.objects.get(pk=motor_id, country=pais)
        except (MotorVehiculo.DoesNotExist, ValueError):
            raise forms.ValidationError("Motor no válido")

        self._motor_empresa_obj = None
        if modelo and hasattr(motor, "modelos") and not motor.modelos.filter(pk=modelo.pk).exists():
            motor.modelos.add(modelo)

        return motor

    def clean_caja(self):
        """Aceptar cajas globales o privadas con prefijo empresa:<id>."""
        raw_value = (self.cleaned_data.get("caja") or "").strip()
        empresa = getattr(self.user, "empresa", None)
        pais = self._resolve_country(self.user, self.request, default="CL")
        modelo = self.cleaned_data.get("modelo")

        if not raw_value:
            self._caja_empresa_obj = None
            return None

        if raw_value.startswith("empresa:"):
            if not empresa or not modelo:
                raise forms.ValidationError("Caja privada no válida para esta empresa/modelo")
            private_id = raw_value.split(":", 1)[1]
            try:
                caja_privada = CajaVehiculoEmpresa.objects.get(
                    pk=private_id,
                    empresa=empresa,
                    modelo=modelo,
                    country=pais,
                )
            except (CajaVehiculoEmpresa.DoesNotExist, ValueError):
                raise forms.ValidationError("Caja privada no válida")
            self._caja_empresa_obj = caja_privada
            return None

        caja_id = raw_value.split(":", 1)[1] if raw_value.startswith("global:") else raw_value
        try:
            caja = CajaVehiculo.objects.get(pk=caja_id, country=pais)
        except (CajaVehiculo.DoesNotExist, ValueError):
            raise forms.ValidationError("Caja no válida")

        self._caja_empresa_obj = None
        if modelo and hasattr(caja, "modelos") and not caja.modelos.filter(pk=modelo.pk).exists():
            caja.modelos.add(modelo)

        return caja

    def save(self, commit=True):
        """Guardar el vehículo con manejo especial de campos personalizados"""
        vehiculo = super().save(commit=False)
        request = getattr(self, "request", None)
        empresa = getattr(self.user, "empresa", None)
        pais = self._resolve_country(self.user, self.request, default="CL")

        modelo = self.cleaned_data.get("modelo")
        motor_nombre = (
            getattr(self, "_pending_motor_nombre", "")
            or (request.POST.get("motor_nuevo") if request else "")
            or (request.POST.get("nuevo_motor") if request else "")
        )
        caja_nombre = (
            getattr(self, "_pending_caja_nombre", "")
            or (request.POST.get("caja_nuevo") if request else "")
            or (request.POST.get("nuevo_caja") if request else "")
        )
        motor_nombre = str(motor_nombre or "").strip()
        caja_nombre = str(caja_nombre or "").strip()

        # Tipo carrocería (custom)
        if (
            getattr(self, "_tipo_carroceria_nuevo", False)
            and request
            and request.POST.get("nuevo_tipo_carroceria")
        ):
            vehiculo.tipo_carroceria = (
                request.POST.get("nuevo_tipo_carroceria") or ""
            ).strip() or None

        # Color
        if getattr(self, "_color_nuevo", False) and request and request.POST.get("nuevo_color"):
            kwargs = {"nombre": request.POST["nuevo_color"]}
            if hasattr(ColorVehiculo, "country"):
                kwargs["country"] = pais
            if hasattr(ColorVehiculo, "empresa") and empresa:
                kwargs["empresa"] = empresa
            color_obj, _ = ColorVehiculo.objects.get_or_create(**kwargs)
            vehiculo.color = color_obj

        # Motor
        if motor_nombre:
            if empresa and modelo:
                motor_obj, _ = MotorVehiculoEmpresa.objects.get_or_create(
                    empresa=empresa,
                    modelo=modelo,
                    country=pais,
                    nombre=motor_nombre,
                )
                vehiculo.motor = None
                vehiculo.motor_empresa = motor_obj
            else:
                kwargs = {"nombre": motor_nombre}
                if hasattr(MotorVehiculo, "country"):
                    kwargs["country"] = pais
                motor_obj, _ = MotorVehiculo.objects.get_or_create(**kwargs)
                vehiculo.motor = motor_obj
                vehiculo.motor_empresa = None
                if modelo and hasattr(motor_obj, "modelos"):
                    motor_obj.modelos.add(modelo)
        else:
            vehiculo.motor_empresa = getattr(self, "_motor_empresa_obj", None)

        # Caja
        if caja_nombre:
            if empresa and modelo:
                caja_obj, _ = CajaVehiculoEmpresa.objects.get_or_create(
                    empresa=empresa,
                    modelo=modelo,
                    country=pais,
                    nombre=caja_nombre,
                )
                vehiculo.caja = None
                vehiculo.caja_empresa = caja_obj
            else:
                kwargs = {"nombre": caja_nombre}
                if hasattr(CajaVehiculo, "country"):
                    kwargs["country"] = pais
                caja_obj, _ = CajaVehiculo.objects.get_or_create(**kwargs)
                vehiculo.caja = caja_obj
                vehiculo.caja_empresa = None
                if modelo and hasattr(caja_obj, "modelos"):
                    caja_obj.modelos.add(modelo)
        else:
            vehiculo.caja_empresa = getattr(self, "_caja_empresa_obj", None)

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
            "tipo_carroceria",
        ]
        widgets = {
            "patente": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400",
                    "style": "text-transform:uppercase;",
                    "oninput": "this.value=this.value.toUpperCase()"
                }
            ),
            "vin": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400",
                    "style": "text-transform:uppercase;",
                    "oninput": "this.value=this.value.toUpperCase()"
                }
            ),
            "tipo_carroceria": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400",
                    "placeholder": "Ej: Sedan, SUV, Pickup, Hatchback, Coupe",
                }
            ),
        }
