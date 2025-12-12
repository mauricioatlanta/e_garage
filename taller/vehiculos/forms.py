from datetime import date

from dal import autocomplete
from django.db.models import Q

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

    # Campo cliente explícitamente definido con autocomplete
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.none(),  # Se configurará en __init__
        widget=autocomplete.ModelSelect2(
            url="taller:vehiculos:cliente_autocomplete",
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

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        assert self.user is not None, "VehiculoForm requiere user=..."

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

        # Filtrar clientes por empresa
        if "cliente" in self.fields:
            if empresa:
                self.fields["cliente"].queryset = Cliente.objects.filter(empresa=empresa).order_by(
                    "nombre", "apellido"
                )
            else:
                # Si no hay empresa, usar queryset vacío (el autocomplete lo manejará)
                self.fields["cliente"].queryset = Cliente.objects.none()

            # Asegurar que el widget tenga la URL correcta del autocomplete según el país
            # Si tenemos request, ajustar la URL según el namespace del país
            if self.request and hasattr(self.fields["cliente"].widget, "url"):
                path = (self.request.path or "").lower()
                import logging
                from django.urls import reverse

                log = logging.getLogger(__name__)

                # Determinar el namespace correcto según el país
                if path.startswith("/us/"):
                    # Para USA, usar el namespace usa:vehiculos:cliente_autocomplete
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
                    # Intentar generar la URL absoluta con reverse para asegurar que tenga el prefijo correcto
                    try:
                        absolute_url = reverse(autocomplete_url)
                        log.info(f"[VehiculoForm] URL generada por reverse: {absolute_url}")

                        # Verificar si la URL ya tiene el prefijo correcto
                        expected_prefix = (
                            "/us/"
                            if path.startswith("/us/")
                            else "/cl/" if path.startswith("/cl/") else None
                        )

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
                    except Exception as reverse_error:
                        log.warning(
                            f"[VehiculoForm] No se pudo generar URL absoluta: {reverse_error}, usando namespace: {autocomplete_url}"
                        )

                    # También establecer el namespace para que DAL lo use
                    self.fields["cliente"].widget.url = autocomplete_url
                    log.info(
                        f"[VehiculoForm] ✅ URL de autocomplete cliente actualizada: {autocomplete_url}"
                    )
                except Exception as e:
                    log.error(f"[VehiculoForm] ❌ Error al actualizar URL de autocomplete: {e}")

        # Configurar campo color
        self._configurar_color(pais)

        # Debug: Log del país detectado
        import logging

        log = logging.getLogger(__name__)
        log.info(
            f"[VehiculoForm] País detectado: {pais} (path: {getattr(self.request, 'path', 'N/A') if self.request else 'N/A'})"
        )

        # Etiqueta de año según el país (UX)
        if pais == "US":
            self.fields["anio"].label = "Year"
            log.info("[VehiculoForm] Configurando campos USA")
            self._configurar_campos_usa()
        else:
            log.info(f"[VehiculoForm] Configurando campos LATAM para país: {pais}")
            self._configurar_campos_latam(pais)

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
        import logging

        log = logging.getLogger(__name__)

        empresa = getattr(self.user, "empresa", None)

        # Eliminar el campo marca si ya existe (del Meta) para reemplazarlo
        if "marca" in self.fields:
            log.info("[VehiculoForm._configurar_campos_usa] Eliminando campo marca existente")
            del self.fields["marca"]

        # Campo marca para USA - Usar CatalogoModeloAuto como fuente principal
        try:
            from taller.models.catalogo import CatalogoModeloAuto

            log.info("[VehiculoForm._configurar_campos_usa] Intentando obtener marcas del catálogo")
            # Obtener marcas únicas del catálogo
            marcas_catalogo = CatalogoModeloAuto.get_marcas_activas()

            # Convertir a lista para verificar si hay resultados (ValuesListQuerySet no tiene .exists())
            try:
                marcas_list = list(marcas_catalogo[:500])  # Limitar a 500 para performance
                log.info(
                    f"[VehiculoForm._configurar_campos_usa] Marcas en catálogo: {len(marcas_list)}"
                )
            except Exception as e:
                log.error(
                    f"[VehiculoForm._configurar_campos_usa] Error al obtener marcas del catálogo: {e}"
                )
                marcas_list = []

            if marcas_list:
                log.info(
                    f"[VehiculoForm._configurar_campos_usa] Usando catálogo como fuente ({len(marcas_list)} marcas)"
                )
                # Usar catálogo como fuente principal
                marcas_choices = [("", "Select a brand")] + [
                    (marca, marca) for marca in marcas_list
                ]

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
            else:
                # Fallback: usar modelo Marca si el catálogo está vacío
                log.info(
                    "[VehiculoForm._configurar_campos_usa] Catálogo vacío, usando fallback al modelo Marca"
                )

                # ✅ CRÍTICO: Evaluar el queryset COMPLETO inmediatamente como lista
                marcas_usa = Marca.objects.filter(country="US").order_by("nombre")
                total_marcas = marcas_usa.count()
                log.info(
                    f"[VehiculoForm._configurar_campos_usa] Marcas en modelo Marca (country='US'): {total_marcas}"
                )

                # ✅ Convertir el queryset completo a lista ANTES de crear el campo
                marcas_list = list(marcas_usa)
                log.info(
                    f"[VehiculoForm._configurar_campos_usa] Marcas convertidas a lista: {len(marcas_list)} marcas"
                )

                if len(marcas_list) > 0:
                    log.info(
                        f"[VehiculoForm._configurar_campos_usa] Primeras 5 marcas: {[m.nombre for m in marcas_list[:5]]}"
                    )

                    # ✅ Crear choices con la lista ya materializada
                    marcas_choices = [("", "Select a brand")]
                    for marca in marcas_list:
                        # ✅ VALIDACIÓN: Asegurar que la marca tenga nombre válido y no sea solo un número
                        marca_nombre = marca.nombre.strip() if marca.nombre else ""
                        marca_id_str = str(marca.pk).strip()

                        # Validar que el nombre no sea solo un número (posible error de datos)
                        if marca_nombre and marca_id_str and not marca_nombre.isdigit():
                            marcas_choices.append((marca_id_str, marca_nombre))
                        else:
                            log.warning(
                                f"[VehiculoForm._configurar_campos_usa] ⚠️ Marca con ID {marca.pk} tiene nombre inválido '{marca_nombre}' (es solo número o vacío), omitiendo"
                            )

                    log.info(
                        f"[VehiculoForm._configurar_campos_usa] Choices creadas: {len(marcas_choices)} opciones"
                    )
                    log.info(
                        f"[VehiculoForm._configurar_campos_usa] Primera choice: {marcas_choices[0]}, Segunda: {marcas_choices[1] if len(marcas_choices) > 1 else 'N/A'}"
                    )

                    # ✅ Usar tupla para forzar materialización completa
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

                    # ✅ Verificación final inmediata
                    final_choices = list(self.fields["marca"].choices)
                    log.info(
                        f"[VehiculoForm._configurar_campos_usa] ✅ Campo creado - Verificación final: {len(final_choices)} opciones"
                    )
                    if len(final_choices) > 1:
                        log.info(
                            f"[VehiculoForm._configurar_campos_usa] Primeras 3 choices verificadas: {final_choices[:3]}"
                        )
                    else:
                        log.error(
                            f"[VehiculoForm._configurar_campos_usa] ❌ ERROR CRÍTICO: Campo solo tiene {len(final_choices)} opción después de crear!"
                        )
                        log.error(
                            f"[VehiculoForm._configurar_campos_usa] Choices que intentamos asignar: {marcas_choices[:3]}"
                        )
                        # Forzar reasignación directa
                        self.fields["marca"].choices = marcas_choices_tuple
                        log.info(
                            f"[VehiculoForm._configurar_campos_usa] Reasignadas choices forzadamente"
                        )
                else:
                    # No hay marcas ni en catálogo ni en modelo Marca - crear campo vacío con mensaje
                    log.error(
                        "[VehiculoForm._configurar_campos_usa] ❌ No hay marcas disponibles en catálogo ni en modelo Marca"
                    )
                    log.error(
                        "[VehiculoForm._configurar_campos_usa] 💡 Ejecutar: python manage.py cargar_marcas_usa"
                    )
                    self.fields["marca"] = forms.ChoiceField(
                        choices=[
                            ("", "No brands available - Run: python manage.py cargar_marcas_usa")
                        ],
                        required=True,
                        label="Brand",
                        widget=forms.Select(
                            attrs={
                                "class": "w-full px-4 py-3 rounded-lg bg-black border border-red-500/30 text-red-200 focus:outline-none focus:ring-2 focus:ring-red-400/50 focus:border-red-400"
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

        self.fields["motor"] = forms.ModelChoiceField(
            queryset=MotorVehiculo.objects.filter(country=pais),
            required=False,
            label="Engine",
            widget=autocomplete.ModelSelect2(
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

        self.fields["caja"] = forms.ModelChoiceField(
            queryset=CajaVehiculo.objects.filter(country=pais),
            required=False,
            label="Transmission",
            widget=autocomplete.ModelSelect2(
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

        self.fields["motor"] = forms.ModelChoiceField(
            queryset=MotorVehiculo.objects.filter(country=pais),
            required=False,
            label="Motor",
            widget=autocomplete.ModelSelect2(
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

        self.fields["caja"] = forms.ModelChoiceField(
            queryset=CajaVehiculo.objects.filter(country=pais),
            required=False,
            label="Transmisión",
            widget=autocomplete.ModelSelect2(
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
                motores_modelo = MotorVehiculo.objects.filter(modelos=modelo_actual).order_by(
                    "nombre"
                )

                # ✅ Incluir motor actual si existe, aunque no esté asociado al modelo
                # Esto asegura que el valor actual se muestre al editar
                if self.instance and self.instance.motor_id:
                    # Usar union para incluir el motor actual
                    motores_modelo = MotorVehiculo.objects.filter(
                        Q(modelos=modelo_actual) | Q(pk=self.instance.motor_id)
                    ).order_by("nombre")

                # ✅ Actualizar queryset del campo (ModelChoiceField con autocomplete)
                # El widget autocomplete maneja la creación de nuevos items via data-tags
                self.fields["motor"].queryset = motores_modelo

                # Cargar cajas del modelo
                cajas_modelo = CajaVehiculo.objects.filter(modelos=modelo_actual).order_by("nombre")

                # ✅ Incluir caja actual si existe, aunque no esté asociada al modelo
                # Esto asegura que el valor actual se muestre al editar
                if self.instance and self.instance.caja_id:
                    # Usar union para incluir la caja actual
                    cajas_modelo = CajaVehiculo.objects.filter(
                        Q(modelos=modelo_actual) | Q(pk=self.instance.caja_id)
                    ).order_by("nombre")

                # ✅ Actualizar queryset del campo (ModelChoiceField con autocomplete)
                # El widget autocomplete maneja la creación de nuevos items via data-tags
                self.fields["caja"].queryset = cajas_modelo
            else:
                # Si no hay modelo, asegurar que el motor y caja actuales estén en el queryset
                if self.instance and self.instance.motor_id:
                    # Incluir solo el motor actual si no hay modelo
                    self.fields["motor"].queryset = MotorVehiculo.objects.filter(
                        Q(pk=self.instance.motor_id)
                    )
                if self.instance and self.instance.caja_id:
                    # Incluir solo la caja actual si no hay modelo
                    self.fields["caja"].queryset = CajaVehiculo.objects.filter(
                        Q(pk=self.instance.caja_id)
                    )

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
        """Manejar motor - ahora es ModelChoiceField, recibe instancia directamente"""
        motor = self.cleaned_data.get("motor")

        # Si está vacío o es None, retornar None
        if not motor:
            return None

        # ✅ Verificar pertenencia al modelo seleccionado (si tu relación es M2M 'modelos')
        modelo = self.cleaned_data.get("modelo")
        if modelo and hasattr(motor, "modelos"):
            # Si el motor no está asociado al modelo, asociarlo automáticamente
            if not motor.modelos.filter(pk=modelo.pk).exists():
                motor.modelos.add(modelo)

        return motor

    def clean_caja(self):
        """Manejar caja - ahora es ModelChoiceField, recibe instancia directamente"""
        caja = self.cleaned_data.get("caja")

        # Si está vacío o es None, retornar None
        if not caja:
            return None

        # ✅ Verificar pertenencia al modelo seleccionado (M2M 'modelos')
        modelo = self.cleaned_data.get("modelo")
        if modelo and hasattr(caja, "modelos"):
            # Si la caja no está asociada al modelo, asociarla automáticamente
            if not caja.modelos.filter(pk=modelo.pk).exists():
                caja.modelos.add(modelo)

        return caja

    def save(self, commit=True):
        """Guardar el vehículo con manejo especial de campos personalizados"""
        vehiculo = super().save(commit=False)
        request = getattr(self, "request", None)
        empresa = getattr(self.user, "empresa", None)
        pais = (getattr(empresa, "pais", None) or "CL").strip().upper()

        modelo = self.cleaned_data.get("modelo")

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
        if getattr(self, "_motor_nuevo", False) and request and request.POST.get("nuevo_motor"):
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
        if getattr(self, "_caja_nuevo", False) and request and request.POST.get("nuevo_caja"):
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
