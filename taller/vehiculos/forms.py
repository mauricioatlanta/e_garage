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
    # La URL se configurará dinámicamente en __init__ según el país
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.none(),  # Se configurará en __init__
        widget=autocomplete.ModelSelect2(
            url="chile:vehiculos:cliente_autocomplete",  # Default para Chile, se ajustará en __init__
            attrs={
                "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400",
                "data-placeholder": "Escribe para buscar…",
                "data-minimum-input-length": 1,
                "data-allow-clear": "true",
            },
        ),
        required=False,
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
            # Para vehículo de desarme, cliente es opcional; para cliente es obligatorio
            if "tipo_uso" in self.fields:
                tipo = (
                    (self.data.get("tipo_uso") if self.data else None)
                    or self.initial.get("tipo_uso")
                    or "cliente"
                )
                self.fields["cliente"].required = tipo != "desarme"

            # Asegurar que el widget tenga la URL correcta del autocomplete según el país
            # Si tenemos request, ajustar la URL según el namespace del país
            if self.request and hasattr(self.fields["cliente"].widget, "url"):
                path = (self.request.path or "").lower()
                import logging
                from django.urls import reverse

                log = logging.getLogger(__name__)

                # Determinar el namespace correcto según el país
                # /us/en/ y /us/es/ usan us_en/us_es (taller.urls); /us/ sin idioma usa "usa"
                if path.startswith("/us/en/"):
                    autocomplete_url = "us_en:vehiculos:cliente_autocomplete"
                    log.info(
                        f"[VehiculoForm] Configurando URL de autocomplete cliente para US EN: {autocomplete_url}"
                    )
                elif path.startswith("/us/es/"):
                    autocomplete_url = "us_es:vehiculos:cliente_autocomplete"
                    log.info(
                        f"[VehiculoForm] Configurando URL de autocomplete cliente para US ES: {autocomplete_url}"
                    )
                elif path.startswith("/us/"):
                    # USA sin prefijo de idioma (ej. /us/vehiculos/...)
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
        """Configurar campos específicos para usuarios de USA."""
        from taller.models.marca import Marca
        from taller.models.extras_vehiculo import CajaVehiculo, MotorVehiculo
        import logging

        log = logging.getLogger(__name__)

        # Eliminar el campo marca si ya existe (del Meta) para reemplazarlo
        if "marca" in self.fields:
            log.info("[VehiculoForm._configurar_campos_usa] Eliminando campo marca existente")
            del self.fields["marca"]

        # Marca: ahora se carga dinámicamente por año vía JS
        self.fields["marca"] = forms.ChoiceField(
            choices=[("", "Select year first")],
            required=False,
            label="Brand",
            widget=forms.Select(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400",
                    "data-requires-year": "1",
                }
            ),
        )

        # Modelo: se carga dinámicamente por marca + año vía JS
        self.fields["modelo"] = forms.CharField(
            required=False,
            label="Model",
            widget=forms.Select(
                choices=[("", "Select brand first")],
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400",
                    "data-requires-brand": "1",
                },
            ),
        )

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

        # Configurar valores iniciales si estamos editando o repoblando POST
        self._configurar_valores_iniciales_usa()

        # Restaurar valores iniciales de campos básicos si estamos editando
        if self.instance and self.instance.pk:
            if hasattr(self.instance, "patente"):
                self.fields["patente"].initial = self.instance.patente
            if hasattr(self.instance, "vin"):
                self.fields["vin"].initial = self.instance.vin
            if hasattr(self.instance, "anio") and self.instance.anio:
                self.fields["anio"].initial = str(self.instance.anio)
            if hasattr(self.instance, "millas") and self.instance.millas is not None:
                self.fields["millas"].initial = self.instance.millas
            if hasattr(self.instance, "cliente_id") and self.instance.cliente_id:
                if self.instance.cliente_id not in [c.pk for c in self.fields["cliente"].queryset]:
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
        """Configurar valores iniciales para usuarios de USA."""
        from taller.models.marca import Marca
        from taller.models.modelo import Modelo
        from taller.models.extras_vehiculo import CajaVehiculo, MotorVehiculo

        if self.instance and self.instance.pk:
            # Año inicial
            if getattr(self.instance, "anio", None):
                self.fields["anio"].initial = str(self.instance.anio)

            # Marca inicial
            marca_inicial = None
            if getattr(self.instance, "marca_id", None):
                marca_inicial = self.instance.marca.nombre
            elif getattr(self.instance, "marca_texto", None):
                marca_inicial = self.instance.marca_texto

            # Modelo inicial
            modelo_inicial = None
            if getattr(self.instance, "modelo_id", None):
                modelo_inicial = self.instance.modelo.nombre
            elif getattr(self.instance, "modelo_texto", None):
                modelo_inicial = self.instance.modelo_texto

            # Poblar marca si estamos editando
            if marca_inicial:
                self.fields["marca"].choices = [
                    ("", "Select year first"),
                    (marca_inicial, marca_inicial),
                    (NEW_SENTINEL, "Other / Enter manually"),
                ]
                self.fields["marca"].initial = marca_inicial

            # Poblar modelo si estamos editando
            if modelo_inicial:
                self.fields["modelo"].widget.choices = [
                    ("", "Select brand first"),
                    (modelo_inicial, modelo_inicial),
                    (NEW_SENTINEL, "Other / Enter manually"),
                ]
                self.fields["modelo"].initial = modelo_inicial

            # Si hay POST, priorizar lo enviado
            if self.data:
                marca_post = (self.data.get("marca") or "").strip()
                modelo_post = (self.data.get("modelo") or "").strip()

                if marca_post:
                    marca_choices = [("", "Select year first")]
                    if marca_post not in [c[0] for c in marca_choices]:
                        marca_choices.append((marca_post, marca_post))
                    marca_choices.append((NEW_SENTINEL, "Other / Enter manually"))
                    self.fields["marca"].choices = marca_choices
                    self.fields["marca"].initial = marca_post

                if modelo_post:
                    modelo_choices = [("", "Select brand first")]
                    if modelo_post not in [c[0] for c in modelo_choices]:
                        modelo_choices.append((modelo_post, modelo_post))
                    modelo_choices.append((NEW_SENTINEL, "Other / Enter manually"))
                    self.fields["modelo"].widget.choices = modelo_choices
                    self.fields["modelo"].initial = modelo_post

            # Cargar motores y cajas del modelo actual si existe
            modelo_actual = None

            if self.instance and hasattr(self.instance, "modelo"):
                modelo_actual = getattr(self.instance, "modelo", None)

            if self.data and "modelo" in self.data:
                modelo_post = (self.data.get("modelo") or "").strip()
                if modelo_post.isdigit():
                    try:
                        modelo_actual = Modelo.objects.get(pk=int(modelo_post))
                    except Exception:
                        pass

            if modelo_actual:
                motores_modelo = MotorVehiculo.objects.filter(modelos=modelo_actual).order_by(
                    "nombre"
                )
                if self.instance and self.instance.motor_id:
                    motores_modelo = MotorVehiculo.objects.filter(
                        Q(modelos=modelo_actual) | Q(pk=self.instance.motor_id)
                    ).order_by("nombre")
                self.fields["motor"].queryset = motores_modelo

                cajas_modelo = CajaVehiculo.objects.filter(modelos=modelo_actual).order_by("nombre")
                if self.instance and self.instance.caja_id:
                    cajas_modelo = CajaVehiculo.objects.filter(
                        Q(modelos=modelo_actual) | Q(pk=self.instance.caja_id)
                    ).order_by("nombre")
                self.fields["caja"].queryset = cajas_modelo
            else:
                if self.instance and self.instance.motor_id:
                    self.fields["motor"].queryset = MotorVehiculo.objects.filter(
                        pk=self.instance.motor_id
                    )
                if self.instance and self.instance.caja_id:
                    self.fields["caja"].queryset = CajaVehiculo.objects.filter(
                        pk=self.instance.caja_id
                    )

            motor_initial = None
            if self.instance.motor_id:
                motor_initial = str(self.instance.motor_id)
            elif self.data and "motor" in self.data:
                motor_initial = self.data.get("motor")
            if motor_initial:
                self.fields["motor"].initial = motor_initial

            caja_initial = None
            if self.instance.caja_id:
                caja_initial = str(self.instance.caja_id)
            elif self.data and "caja" in self.data:
                caja_initial = self.data.get("caja")
            if caja_initial:
                self.fields["caja"].initial = caja_initial

        else:
            # Crear vehículo: si hay POST con errores, repoblar selects
            if self.data:
                anio_val = (self.data.get("anio") or "").strip()
                marca_val = (self.data.get("marca") or "").strip()
                modelo_val = (self.data.get("modelo") or "").strip()

                # Marca
                if marca_val:
                    marca_choices = [("", "Select year first")]
                    marca_choices.append((marca_val, marca_val))
                    marca_choices.append((NEW_SENTINEL, "Other / Enter manually"))
                    self.fields["marca"].choices = marca_choices
                    self.fields["marca"].initial = marca_val

                # Modelo
                if modelo_val:
                    modelo_choices = [("", "Select brand first")]
                    modelo_choices.append((modelo_val, modelo_val))
                    modelo_choices.append((NEW_SENTINEL, "Other / Enter manually"))
                    self.fields["modelo"].widget.choices = modelo_choices
                    self.fields["modelo"].initial = modelo_val

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

        # Desarme: fecha de ingreso obligatoria cuando tipo_uso es desarme
        tipo_uso = (cleaned_data.get("tipo_uso") or "").strip() or "cliente"
        if tipo_uso == "desarme" and not cleaned_data.get("fecha_ingreso_desarme"):
            self.add_error(
                "fecha_ingreso_desarme",
                "Para vehículos de desarme debe indicar la fecha de ingreso.",
            )

        return cleaned_data

    def clean_marca(self):
        """Convertir ID/nombre de marca a instancia."""
        empresa = getattr(self.user, "empresa", None)
        pais = (getattr(empresa, "pais", None) or "CL").strip().upper()

        if self.request:
            path = (self.request.path or "").lower()
            if path.startswith("/us/"):
                pais = "US"
            elif path.startswith("/cl/"):
                pais = "CL"
            elif path.startswith("/mx/"):
                pais = "MX"

        val = self.cleaned_data.get("marca")
        from taller.models.marca import Marca

        # USA: acepta string del catálogo, ID legacy o manual
        if pais == "US":
            nuevo_marca = (
                (self.data or {}).get("nuevo_marca")
                or (self.data or {}).get("marca_nuevo")
                or (self.data or {}).get("nuevo_marca_texto")
                or ""
            ).strip()

            if val == NEW_SENTINEL:
                if not nuevo_marca:
                    raise forms.ValidationError("Enter a brand or select one from the list.")
                obj, _ = Marca.objects.get_or_create(
                    nombre=nuevo_marca,
                    country="US",
                    defaults={"nombre": nuevo_marca, "country": "US"},
                )
                return obj

            if not val and nuevo_marca:
                obj, _ = Marca.objects.get_or_create(
                    nombre=nuevo_marca,
                    country="US",
                    defaults={"nombre": nuevo_marca, "country": "US"},
                )
                return obj

            if not val:
                raise forms.ValidationError("Select a brand or enter one manually.")

            if isinstance(val, Marca):
                return val

            if isinstance(val, str):
                val = val.strip()

                # Intentar como ID numérico legacy
                if val.isdigit():
                    try:
                        return Marca.objects.get(pk=int(val), country="US")
                    except Marca.DoesNotExist:
                        raise forms.ValidationError(f"Brand with ID {val} not found for USA.")

                # String de catálogo
                obj, _ = Marca.objects.get_or_create(
                    nombre=val,
                    country="US",
                    defaults={"nombre": val, "country": "US"},
                )
                return obj

            if isinstance(val, int):
                try:
                    return Marca.objects.get(pk=val, country="US")
                except Marca.DoesNotExist:
                    raise forms.ValidationError(f"Brand with ID {val} not found for USA.")

            obj, _ = Marca.objects.get_or_create(
                nombre=str(val).strip(),
                country="US",
                defaults={"nombre": str(val).strip(), "country": "US"},
            )
            return obj

        # Chile/México/LATAM: comportamiento actual
        if not val:
            raise forms.ValidationError("Debe seleccionar una marca")

        try:
            if isinstance(val, str):
                try:
                    marca_id = int(val)
                    return Marca.objects.get(pk=marca_id, country=pais)
                except (ValueError, TypeError):
                    pass
            elif isinstance(val, int):
                return Marca.objects.get(pk=val, country=pais)

            return Marca.objects.get(nombre=val, country=pais)

        except Marca.DoesNotExist:
            raise forms.ValidationError(f"Marca no válida para {pais}")

    def clean_modelo(self):
        """Convertir ID/nombre de modelo a instancia."""
        empresa = getattr(self.user, "empresa", None)
        pais = (getattr(empresa, "pais", None) or "CL").strip().upper()

        if self.request:
            path = (self.request.path or "").lower()
            if path.startswith("/us/"):
                pais = "US"
            elif path.startswith("/cl/"):
                pais = "CL"
            elif path.startswith("/mx/"):
                pais = "MX"

        val = self.cleaned_data.get("modelo")
        from taller.models.modelo import Modelo
        from taller.models.marca import Marca
        import logging

        log = logging.getLogger(__name__)

        # USA: acepta string del catálogo, ID legacy o manual
        if pais == "US":
            nuevo_modelo = (
                (self.data or {}).get("nuevo_modelo")
                or (self.data or {}).get("modelo_nuevo")
                or (self.data or {}).get("nuevo_modelo_texto")
                or ""
            ).strip()

            marca = self.cleaned_data.get("marca")

            if val == NEW_SENTINEL:
                if not nuevo_modelo:
                    raise forms.ValidationError("Enter a model or select one from the list.")
                if not marca or not isinstance(marca, Marca):
                    raise forms.ValidationError("Select or enter a brand first.")
                obj, _ = Modelo.objects.get_or_create(
                    marca=marca,
                    nombre=nuevo_modelo,
                    country="US",
                    defaults={"nombre": nuevo_modelo, "marca": marca, "country": "US"},
                )
                return obj

            if not val and nuevo_modelo:
                if not marca or not isinstance(marca, Marca):
                    raise forms.ValidationError("Select or enter a brand first.")
                obj, _ = Modelo.objects.get_or_create(
                    marca=marca,
                    nombre=nuevo_modelo,
                    country="US",
                    defaults={"nombre": nuevo_modelo, "marca": marca, "country": "US"},
                )
                return obj

            if not val:
                raise forms.ValidationError("Select a model or enter one manually.")

            if isinstance(val, Modelo):
                return val

            # ID numérico legacy
            if isinstance(val, str):
                val = val.strip()
                if val.isdigit():
                    try:
                        obj = Modelo.objects.select_related("marca").get(pk=int(val), country="US")
                        if marca and isinstance(marca, Marca) and obj.marca_id != marca.id:
                            raise forms.ValidationError(
                                f"The model '{obj.nombre}' does not belong to the selected brand '{marca.nombre}'."
                            )
                        return obj
                    except Modelo.DoesNotExist:
                        raise forms.ValidationError(f"Model with ID {val} not found for USA.")

                # String de catálogo
                if not marca or not isinstance(marca, Marca):
                    raise forms.ValidationError("Select or enter a brand first.")

                obj, _ = Modelo.objects.get_or_create(
                    marca=marca,
                    nombre=val,
                    country="US",
                    defaults={"nombre": val, "marca": marca, "country": "US"},
                )
                return obj

            if isinstance(val, int):
                try:
                    obj = Modelo.objects.select_related("marca").get(pk=val, country="US")
                    if marca and isinstance(marca, Marca) and obj.marca_id != marca.id:
                        raise forms.ValidationError(
                            f"The model '{obj.nombre}' does not belong to the selected brand '{marca.nombre}'."
                        )
                    return obj
                except Modelo.DoesNotExist:
                    raise forms.ValidationError(f"Model with ID {val} not found for USA.")

            log.error(f"[clean_modelo] Invalid USA model value: {val!r}")
            raise forms.ValidationError("Invalid model value.")

        # Chile/México/LATAM: comportamiento actual
        if not val:
            raise forms.ValidationError("Debe seleccionar un modelo")

        try:
            if isinstance(val, Modelo):
                return val

            modelo_id = int(val)

            obj = Modelo.objects.select_related("marca").get(pk=modelo_id, country=pais)

            marca = self.cleaned_data.get("marca")
            if marca and isinstance(marca, Marca):
                if obj.marca_id != marca.id:
                    raise forms.ValidationError(
                        f"El modelo '{obj.nombre}' no pertenece a la marca '{marca.nombre}' seleccionada."
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

    @property
    def media(self):
        """Deduplica Media para evitar DAL/Select2 cargados varias veces (evita 'DAL select2 already registered')."""
        base = super().media
        seen_js = []
        for item in base._js:
            if item not in seen_js:
                seen_js.append(item)
        return forms.Media(css=base._css, js=seen_js)

    class Meta:
        model = Vehiculo
        fields = [
            "tipo_uso",
            "cliente",
            "anio",
            "marca",
            "modelo",
            "patente",
            "vin",
            "color",
            "motor",
            "caja",
            # Campos desarmaduría (solo obligatorio fecha_ingreso_desarme cuando tipo_uso=desarme)
            "fecha_ingreso_desarme",
            "proveedor_nombre",
            "proveedor_rut",
            "proveedor_telefono",
            "precio_compra",
            "costo_transporte",
            "costo_grua",
            "costo_papeles",
            "otros_costos_base",
            "observaciones_desarme",
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
            "fecha_ingreso_desarme": forms.DateInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400",
                    "type": "date",
                }
            ),
            "observaciones_desarme": forms.Textarea(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400",
                    "rows": 2,
                }
            ),
            "proveedor_nombre": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400"
                }
            ),
            "proveedor_rut": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400"
                }
            ),
            "proveedor_telefono": forms.TextInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400"
                }
            ),
            "precio_compra": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "costo_transporte": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "costo_grua": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "costo_papeles": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "otros_costos_base": forms.NumberInput(
                attrs={
                    "class": "w-full px-4 py-3 rounded-lg bg-black border border-emerald-500/30 text-emerald-200 focus:outline-none focus:ring-2 focus:ring-emerald-400/50 focus:border-emerald-400",
                    "step": "0.01",
                    "min": "0",
                }
            ),
        }
