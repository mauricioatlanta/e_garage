"""
Vistas de documentos migradas para usar CountryLangTemplateMixin
Esto reemplaza las vistas FBV que están en views.py con plantillas hardcodeadas
"""

import re
from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib.auth.decorators import login_required
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from django.db.models import (
    Case,
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    Q,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce

from taller.forms.documento_form import DocumentoForm
from taller.mixins import CountryLangTemplateMixin
from taller.models import Documento, Tecnico
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.repuesto import Repuesto
from taller.servicios.models import Servicio, ServicioExterno
from taller.auth.decorators_role import RoleRequiredMixin


LANGUAGE_BY_COUNTRY = {
    "CL": "es",
    "MX": "es",
    "VE": "es",
    "PE": "es",
    "US": "en",
    "BR": "pt",
}


def _reverse_with_request(request, view_name, kwargs=None):
    """
    Resuelve URLs respetando los namespaces activos para que la redirección
    mantenga el prefijo país/idioma (por ejemplo, /cl/es/ vs /cl/).
    """

    if kwargs is None:
        kwargs = {}

    resolver_match = getattr(request, "resolver_match", None)
    namespaces = list(getattr(resolver_match, "namespaces", [])) if resolver_match else []
    tried = []

    # 1) Intentar con la pila exacta de namespaces (desde más específico a menos)
    for depth in range(len(namespaces), -1, -1):
        ns = namespaces[:depth]
        full_name = ":".join(ns + [view_name]) if ns else view_name
        if full_name in tried:
            continue
        tried.append(full_name)
        try:
            return reverse(full_name, kwargs=kwargs)
        except NoReverseMatch:
            continue

    # 2) Intentar con namespaces conocidos de fallback
    fallback_names = [
        f"documentos_cl_es:{view_name}",
        f"documentos_us_en:{view_name}",
        f"documentos:{view_name}",
        f"chile:documentos:{view_name}",
        f"usa:documentos:{view_name}",
        view_name,
    ]

    for name in fallback_names:
        if name in tried:
            continue
        tried.append(name)
        try:
            return reverse(name, kwargs=kwargs)
        except NoReverseMatch:
            continue

    # 3) Como último recurso, relanzar la excepción con todo el contexto
    raise NoReverseMatch(
        f"No se pudo resolver '{view_name}' para namespaces {namespaces}. Intentos: {tried}"
    )


def _normalize_numeric_string(value):
    if value in (None, "", "None"):
        return ""
    if isinstance(value, (int, float, Decimal)):
        return str(value)
    text = str(value).strip()
    if not text:
        return ""
    text = text.replace(" ", "")
    comma = text.rfind(",")
    dot = text.rfind(".")
    if comma > -1 and dot > -1:
        if comma > dot:
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif comma > -1:
        text = text.replace(".", "").replace(",", ".")
    else:
        if text.count(".") > 1:
            last = text.rfind(".")
            text = text[:last].replace(".", "") + "." + text[last + 1 :]
        else:
            text = text.replace(",", "")
    return text


def _to_decimal(value, default=Decimal("0")):
    if isinstance(value, Decimal):
        return value
    normalized = _normalize_numeric_string(value)
    if not normalized:
        return default
    try:
        return Decimal(normalized)
    except (InvalidOperation, ValueError):
        return default


def _to_int(value, default=1):
    try:
        return max(1, int(_to_decimal(value, Decimal(default))))
    except (ValueError, TypeError):
        return default


def _parse_prefixed_items(post_data, prefix, fields):
    pattern = re.compile(
        rf"^{re.escape(prefix)}-(\d+)-({ '|'.join(re.escape(f) for f in fields) })$"
    )
    items = {}
    for key in post_data.keys():
        match = pattern.match(key)
        if not match:
            continue
        index = int(match.group(1))
        field = match.group(2)
        items.setdefault(index, {})[field] = post_data.get(key)
    ordered = []
    for index in sorted(items.keys()):
        ordered.append(items[index])
    return ordered


class DocumentoLineItemsMixin:
    REPUESTO_FIELDS = ("codigo", "nombre", "cantidad", "precio_unitario", "precio_compra")
    SERVICIO_FIELDS = ("nombre", "cantidad", "precio_unitario")
    OTRO_FIELDS = ("proveedor", "descripcion", "costo_interno", "precio_cliente")

    def procesar_items_dinamicos(self, documento, clear_existing=False):
        from taller.models.lineas_documento import (
            LineaOtroServicio,
            LineaRepuesto,
            LineaServicio,
        )

        if clear_existing:
            documento.lineas_repuesto.all().delete()
            documento.lineas_servicio.all().delete()
            documento.lineas_otro_servicio.all().delete()

        repuestos = _parse_prefixed_items(self.request.POST, "rep", self.REPUESTO_FIELDS)
        for data in repuestos:
            codigo = (data.get("codigo") or "").strip()
            nombre = (data.get("nombre") or "").strip()
            if not (codigo or nombre):
                continue
            cantidad = _to_int(data.get("cantidad"), default=1)
            precio_unitario = _to_decimal(data.get("precio_unitario"), Decimal("0"))
            linea = LineaRepuesto(
                documento=documento,
                codigo=codigo or nombre,
                nombre=nombre or codigo,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
            )
            linea.save()

        servicios = _parse_prefixed_items(self.request.POST, "serv", self.SERVICIO_FIELDS)
        for data in servicios:
            nombre = (data.get("nombre") or "").strip()
            if not nombre:
                continue
            cantidad = _to_int(data.get("cantidad"), default=1)
            precio_unitario = _to_decimal(data.get("precio_unitario"), Decimal("0"))
            linea = LineaServicio(
                documento=documento,
                nombre=nombre,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
            )
            linea.save()

        otros = _parse_prefixed_items(self.request.POST, "otr", self.OTRO_FIELDS)
        for data in otros:
            descripcion = (data.get("descripcion") or "").strip()
            proveedor = (data.get("proveedor") or "").strip()
            costo_interno = _to_decimal(data.get("costo_interno"), Decimal("0"))
            precio_cliente = _to_decimal(data.get("precio_cliente"), Decimal("0"))
            has_values = any(
                [
                    descripcion,
                    proveedor,
                    costo_interno != 0,
                    precio_cliente != 0,
                ]
            )
            if not has_values:
                continue
            linea = LineaOtroServicio(
                documento=documento,
                nombre=descripcion or proveedor or "Servicio externo",
                empresa_externa=proveedor or "",
                costo_interno=costo_interno,
                precio_cliente=precio_cliente,
                cantidad=1,
            )
            linea.save()

        if hasattr(documento, "recalcular_totales"):
            documento.recalcular_totales(save=True)


@method_decorator(login_required, name="dispatch")
class DocumentoListView(CountryLangTemplateMixin, ListView):
    """Vista para listar documentos de la empresa"""

    model = Documento
    context_object_name = "documentos"
    base_template_name = "documentos/lista_documentos.html"
    paginate_by = 20

    def get_template_names(self):
        """Forzar template específico para US/EN"""
        if self.request.path.startswith("/us/"):
            template_name = "taller/us/en/documentos/lista_documentos.html"
            print(f"[DEBUG] DocumentoListView - Using US/EN template: {template_name}")
            return [template_name]
        else:
            template_names = super().get_template_names()
            print(f"[DEBUG] DocumentoListView - Using default templates: {template_names}")
            return template_names

    def get_queryset(self):
        """Filtrar documentos por empresa del usuario con filtros funcionales"""
        try:
            empresa = self.request.user.empresa
            base_queryset = (
                Documento.objects.filter(empresa=empresa)
                .select_related("cliente", "vehiculo", "tecnico_responsable")
                .prefetch_related(
                    "lineas_repuesto__repuesto",
                    "lineas_servicio__servicio",
                    "lineas_otro_servicio",
                )
            )

            # === FILTROS FUNCIONALES ===
            # Filtro por cliente (nombre o apellido)
            cliente_search = self.request.GET.get("cliente", "").strip()
            if cliente_search:
                base_queryset = base_queryset.filter(
                    Q(cliente__nombre__icontains=cliente_search) |
                    Q(cliente__apellido__icontains=cliente_search) |
                    Q(cliente__email__icontains=cliente_search)
                )

            # Filtro por vehículo (patente o modelo)
            vehiculo_search = self.request.GET.get("vehiculo", "").strip()
            if vehiculo_search:
                base_queryset = base_queryset.filter(
                    Q(vehiculo__patente__icontains=vehiculo_search) |
                    Q(vehiculo__marca__nombre__icontains=vehiculo_search) |
                    Q(vehiculo__modelo__nombre__icontains=vehiculo_search)
                )

            # Filtro por estado
            estado = self.request.GET.get("estado", "").strip()
            if estado:
                base_queryset = base_queryset.filter(estado=estado.upper())

            # Filtro por tipo
            tipo = self.request.GET.get("tipo", "").strip()
            if tipo:
                base_queryset = base_queryset.filter(tipo=tipo.upper())

            # Filtro por fecha desde
            fecha_desde = self.request.GET.get("desde", "").strip()
            if fecha_desde:
                try:
                    from datetime import datetime
                    fecha_desde_obj = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
                    base_queryset = base_queryset.filter(fecha_emision__gte=fecha_desde_obj)
                except ValueError:
                    pass

            # Filtro por fecha hasta
            fecha_hasta = self.request.GET.get("hasta", "").strip()
            if fecha_hasta:
                try:
                    from datetime import datetime
                    fecha_hasta_obj = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
                    base_queryset = base_queryset.filter(fecha_emision__lte=fecha_hasta_obj)
                except ValueError:
                    pass

            # Filtro por número de documento
            numero = self.request.GET.get("numero", "").strip()
            if numero:
                base_queryset = base_queryset.filter(numero__icontains=numero)

            decimal_zero = Value(
                Decimal("0"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )

            qs = (
                base_queryset.annotate(
                    rep_sum=Coalesce(
                        Sum(
                            ExpressionWrapper(
                                F("lineas_repuesto__cantidad")
                                * F("lineas_repuesto__precio_unitario"),
                                output_field=DecimalField(max_digits=14, decimal_places=2),
                            )
                        ),
                        decimal_zero,
                    ),
                    serv_sum=Coalesce(
                        Sum(
                            ExpressionWrapper(
                                F("lineas_servicio__cantidad")
                                * F("lineas_servicio__precio_unitario"),
                                output_field=DecimalField(max_digits=14, decimal_places=2),
                            )
                        ),
                        decimal_zero,
                    ),
                    otros_sum=Coalesce(
                        Sum(
                            ExpressionWrapper(
                                F("lineas_otro_servicio__cantidad")
                                * F("lineas_otro_servicio__precio_cliente"),
                                output_field=DecimalField(max_digits=14, decimal_places=2),
                            )
                        ),
                        decimal_zero,
                    ),
                    servicios_count=Count("lineas_servicio", distinct=True),
                )
                .annotate(
                    iva_calc=Case(
                        When(
                            empresa__pais__iexact="CL",
                            then=ExpressionWrapper(
                                F("rep_sum")
                                * Value(
                                    Decimal("0.19"),
                                    output_field=DecimalField(max_digits=5, decimal_places=2),
                                ),
                                output_field=DecimalField(max_digits=14, decimal_places=2),
                            ),
                        ),
                        default=decimal_zero,
                        output_field=DecimalField(max_digits=14, decimal_places=2),
                    ),
                )
                .annotate(
                    total_display=Coalesce(
                        F("legacy_total_general"),
                        ExpressionWrapper(
                            F("rep_sum") + F("serv_sum") + F("otros_sum") + F("iva_calc"),
                            output_field=DecimalField(max_digits=14, decimal_places=2),
                        ),
                        decimal_zero,
                    )
                )
                .order_by("-fecha_emision", "-id")
            )

            return qs
        except AttributeError:
            return Documento.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["country"] = getattr(self.request.user.empresa, "pais", "cl").lower()

        # Asignar los valores calculados a las propiedades que el template espera
        documentos = context.get("documentos", [])
        for documento in documentos:
            # Usar los valores calculados en las anotaciones
            if hasattr(documento, "rep_sum"):
                documento.neto_repuestos = documento.rep_sum or Decimal("0")
            else:
                documento.neto_repuestos = Decimal("0")
                
            if hasattr(documento, "serv_sum"):
                documento.neto_servicios = documento.serv_sum or Decimal("0")
            else:
                documento.neto_servicios = Decimal("0")
                
            if hasattr(documento, "otros_sum"):
                documento.neto_otros_servicios = documento.otros_sum or Decimal("0")
            else:
                documento.neto_otros_servicios = Decimal("0")
                
            if hasattr(documento, "iva_calc"):
                documento.tax_amount = documento.iva_calc or Decimal("0")
            else:
                documento.tax_amount = Decimal("0")
                
            # Calcular el total si no existe total_display o si es None/0
            if hasattr(documento, "total_display") and documento.total_display:
                documento.total = documento.total_display
            elif hasattr(documento, "legacy_total_general") and documento.legacy_total_general:
                documento.total = documento.legacy_total_general
            else:
                # Calcular total manualmente si no hay anotación
                neto_rep = getattr(documento, "neto_repuestos", Decimal("0"))
                neto_serv = getattr(documento, "neto_servicios", Decimal("0"))
                neto_otros = getattr(documento, "neto_otros_servicios", Decimal("0"))
                iva = getattr(documento, "tax_amount", Decimal("0"))
                documento.total = neto_rep + neto_serv + neto_otros + iva
            
            # Asegurar que total nunca sea None
            if not documento.total or documento.total is None:
                documento.total = Decimal("0")

        # === KPIs Y ESTADÍSTICAS CALCULADAS ===
        # Usar un queryset separado SIN annotations para las estadísticas
        # IMPORTANTE: Crear un queryset completamente nuevo sin ninguna annotation previa
        empresa = self.request.user.empresa
        # Usar .all() para asegurar que no hay annotations previas
        stats_qs = Documento.objects.filter(empresa=empresa)
        
        # Aplicar los mismos filtros que en get_queryset para que los KPIs reflejen los filtros activos
        cliente_search = self.request.GET.get("cliente", "").strip()
        if cliente_search:
            stats_qs = stats_qs.filter(
                Q(cliente__nombre__icontains=cliente_search) |
                Q(cliente__apellido__icontains=cliente_search) |
                Q(cliente__email__icontains=cliente_search)
            )
        
        vehiculo_search = self.request.GET.get("vehiculo", "").strip()
        if vehiculo_search:
            stats_qs = stats_qs.filter(
                Q(vehiculo__patente__icontains=vehiculo_search) |
                Q(vehiculo__marca__nombre__icontains=vehiculo_search) |
                Q(vehiculo__modelo__nombre__icontains=vehiculo_search)
            )
        
        estado = self.request.GET.get("estado", "").strip()
        if estado:
            stats_qs = stats_qs.filter(estado=estado.upper())
        
        tipo = self.request.GET.get("tipo", "").strip()
        if tipo:
            stats_qs = stats_qs.filter(tipo=tipo.upper())
        
        fecha_desde = self.request.GET.get("desde", "").strip()
        if fecha_desde:
            try:
                from datetime import datetime
                fecha_desde_obj = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
                stats_qs = stats_qs.filter(fecha_emision__gte=fecha_desde_obj)
            except ValueError:
                pass
        
        fecha_hasta = self.request.GET.get("hasta", "").strip()
        if fecha_hasta:
            try:
                from datetime import datetime
                fecha_hasta_obj = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
                stats_qs = stats_qs.filter(fecha_emision__lte=fecha_hasta_obj)
            except ValueError:
                pass
        
        numero = self.request.GET.get("numero", "").strip()
        if numero:
            stats_qs = stats_qs.filter(numero__icontains=numero)

        # Calcular estadísticas con agregaciones (usando el queryset sin annotations)
        from datetime import date, timedelta
        hoy = date.today()
        hace_30_dias = hoy - timedelta(days=30)
        
        # Calcular estadísticas con agregaciones
        # Usar el campo 'legacy_total_general' que es el campo DB real (db_column="total_general")
        # o calcular el total sumando los campos individuales para evitar conflictos
        estadisticas = stats_qs.aggregate(
            total=Count("id"),
            emitidos=Count("id", filter=Q(estado="EMITIDO")),
            borradores=Count("id", filter=Q(estado="BORRADOR")),
            anulados=Count("id", filter=Q(estado="ANULADO")),
            hoy=Count("id", filter=Q(fecha_emision=hoy)),
            ultimos_30_dias=Count("id", filter=Q(fecha_emision__gte=hace_30_dias)),
            pendientes_pago=Count("id", filter=Q(estado_pago="NO_PAGADO", estado="EMITIDO")),
            presupuestos_pendientes=Count("id", filter=Q(tipo="PRES", estado="EMITIDO")),
            ots_sin_cerrar=Count("id", filter=Q(tipo="OT", estado__in=["EMITIDO", "BORRADOR"])),
        )
        
        # Calcular el total sumando los campos individuales para evitar conflictos con annotations
        total_calculado = stats_qs.aggregate(
            sum_rep=Sum("neto_repuestos"),
            sum_serv=Sum("neto_servicios"),
            sum_otros=Sum("neto_otros_servicios"),
            sum_tax=Sum("tax_amount"),
        )
        estadisticas["total_monto"] = (
            (total_calculado["sum_rep"] or Decimal("0")) +
            (total_calculado["sum_serv"] or Decimal("0")) +
            (total_calculado["sum_otros"] or Decimal("0")) +
            (total_calculado["sum_tax"] or Decimal("0"))
        )
        
        context["estadisticas"] = estadisticas
        context["documentos_pendientes"] = estadisticas.get("borradores", 0)
        context["documentos_proceso"] = estadisticas.get("emitidos", 0)
        context["documentos_completados"] = estadisticas.get("emitidos", 0)
        
        # Pasar los valores de filtros al template para mantenerlos en el formulario
        context["filtros_activos"] = {
            "cliente": cliente_search,
            "vehiculo": vehiculo_search,
            "estado": estado,
            "tipo": tipo,
            "desde": fecha_desde,
            "hasta": fecha_hasta,
            "numero": numero,
        }

        return context

    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)


@method_decorator(login_required, name="dispatch")
class DocumentoCreateView(DocumentoLineItemsMixin, CountryLangTemplateMixin, CreateView):
    """Vista para crear documentos"""

    model = Documento
    form_class = DocumentoForm
    base_template_name = "documentos/document_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.request.user.empresa

        # Cargar mecánicos activos del taller
        mecanicos = Tecnico.objects.filter(empresa=empresa, activo=True)

        path = (self.request.path or "").lower()
        path_country = "CL"
        if path.startswith("/us/"):
            path_country = "US"
        elif path.startswith("/mx/"):
            path_country = "MX"
        elif path.startswith("/pe/"):
            path_country = "PE"
        elif path.startswith("/ve/"):
            path_country = "VE"
        elif path.startswith("/br/"):
            path_country = "BR"

        company_country = (
            getattr(self.request, "company_country", None)
            or getattr(empresa, "pais", None)
            or path_country
        )

        country_code = str(company_country).upper() if company_country else "CL"
        language = LANGUAGE_BY_COUNTRY.get(country_code, "es")

        context.update(
            {
                "mecanicos": mecanicos,
                "tecnicos": mecanicos,  # Alias para compatibilidad con templates
                "es_edicion": False,
                "company_country": company_country,
                "today": timezone.now().date(),  # Agregar fecha actual
                "template_name": self.get_template_names()[0],
                "pais_emoji": "🇺🇸" if self.request.path.startswith("/us/") else "🇨🇱",
                "empresa": empresa,
                "total": 0,
                "subtotal_repuestos": 0,
                "subtotal_servicios": 0,
                "subtotal_otros_servicios": 0,
                "iva": 0,
                "repuestos": [],
                "debug": True,  # Habilitar debug en template
            }
        )

        clientes_prefetch = []
        vehiculos_prefetch = []
        repuestos_prefetch = []
        servicios_prefetch = []
        otros_servicios_prefetch = []

        if empresa:
            clientes_qs = (
                Cliente.objects.filter(empresa=empresa)
                .order_by("nombre", "apellido")
                .only("id", "nombre", "apellido", "email", "telefono")
            )
            for cliente in clientes_qs[:50]:
                clientes_prefetch.append(
                    {
                        "id": cliente.id,
                        "nombre": str(cliente),
                        "nombre_completo": str(cliente),
                        "email": cliente.email or "",
                        "telefono": cliente.telefono or "",
                    }
                )

            vehiculos_qs = (
                Vehiculo.objects.filter(empresa=empresa)
                .select_related("cliente", "marca", "modelo")
                .only("id", "cliente_id", "patente", "vin", "anio", "marca", "modelo")
            )
            for vehiculo in vehiculos_qs[:50]:
                label = vehiculo.display_label()
                vehiculos_prefetch.append(
                    {
                        "id": vehiculo.id,
                        "cliente_id": vehiculo.cliente_id,
                        "label": label,
                        "text": label,
                    }
                )

            repuestos_qs = (
                Repuesto.objects.filter(empresa=empresa)
                .order_by("nombre")
                .only("id", "part_number", "nombre", "precio_compra", "precio_venta")
            )
            for repuesto in repuestos_qs[:50]:
                repuestos_prefetch.append(
                    {
                        "id": repuesto.id,
                        "codigo": repuesto.part_number or "",
                        "nombre": repuesto.nombre,
                        "precio_compra": float(repuesto.precio_compra or Decimal("0")),
                        "precio_venta": float(repuesto.precio_venta or Decimal("0")),
                        "precio_venta_sugerido": float(repuesto.precio_venta or Decimal("0")),
                    }
                )

            servicios_qs = (
                Servicio.objects.filter(empresa=empresa, names__language=language)
                .select_related("categoria", "subcategoria")
                .prefetch_related("names", "categoria__names", "subcategoria__names")
                .distinct()
            )
            for servicio in servicios_qs[:50]:
                servicios_prefetch.append(
                    {
                        "id": servicio.id,
                        "nombre": servicio.get_label(language),
                        "categoria": (
                            servicio.categoria.get_label(language) if servicio.categoria else ""
                        ),
                        "categoria_code": servicio.categoria.code if servicio.categoria else "",
                        "subcategoria": (
                            servicio.subcategoria.get_label(language)
                            if servicio.subcategoria
                            else ""
                        ),
                        "subcategoria_code": (
                            servicio.subcategoria.code if servicio.subcategoria else ""
                        ),
                        "precio": 0.0,
                        "precio_sugerido": 0.0,
                        "precio_cliente": 0.0,
                    }
                )

            otros_qs = (
                ServicioExterno.objects.filter(empresa=empresa, activo=True)
                .select_related("categoria", "subcategoria")
                .prefetch_related("categoria__names", "subcategoria__names")
            )
            for externo in otros_qs[:50]:
                otros_servicios_prefetch.append(
                    {
                        "id": externo.id,
                        "nombre": externo.nombre,
                        "empresa": externo.empresa_externa,
                        "empresa_ext": externo.empresa_externa,
                        "categoria": (
                            externo.categoria.get_label(language) if externo.categoria else ""
                        ),
                        "subcategoria": (
                            externo.subcategoria.get_label(language) if externo.subcategoria else ""
                        ),
                        "precio_taller": float(externo.costo_taller or Decimal("0")),
                        "precio_cliente": float(externo.precio_cliente or Decimal("0")),
                    }
                )

        context.update(
            {
                "clientes_prefetch": clientes_prefetch,
                "vehiculos_prefetch": vehiculos_prefetch,
                "repuestos_prefetch": repuestos_prefetch,
                "servicios_prefetch": servicios_prefetch,
                "otros_servicios_prefetch": otros_servicios_prefetch,
            }
        )
        return context

    def get_form_kwargs(self):
        """Obtener argumentos para el formulario"""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["empresa"] = getattr(self.request.user, "empresa", None)
        kwargs["country"] = "US" if self.request.path.startswith("/us/") else "CL"
        return kwargs

    def get_success_url(self):
        """Redirigir a la lista de documentos respetando el prefijo país/idioma."""
        return _reverse_with_request(self.request, "lista_documentos")

    def form_valid(self, form):
        print("[DEBUG DocumentoCreateView] form_valid llamado")
        print(
            f"[DEBUG DocumentoCreateView] Cliente en form.cleaned_data: {form.cleaned_data.get('cliente', 'NO ENCONTRADO')}"
        )
        print(
            f"[DEBUG DocumentoCreateView] Cliente en form.instance: {getattr(form.instance, 'cliente', 'NO ENCONTRADO')}"
        )
        print(
            f"[DEBUG DocumentoCreateView] CSRF token: {self.request.POST.get('csrfmiddlewaretoken', 'NO ENCONTRADO')}"
        )

        form.instance.empresa = self.request.user.empresa

        # Guardar el documento primero
        response = super().form_valid(form)

        # Procesar items dinámicos después de guardar
        self.procesar_items_dinamicos(form.instance, clear_existing=True)

        # Agregar mensaje de éxito
        from django.contrib import messages

        messages.success(
            self.request,
            f"Documento {form.instance.numero_documento} creado exitosamente para {form.instance.cliente.nombre}.",
        )

        return response

    def form_invalid(self, form):
        print("[DEBUG DocumentoCreateView] form_invalid llamado")
        print(f"[DEBUG DocumentoCreateView] Errores: {form.errors}")
        print(f"[DEBUG DocumentoCreateView] Datos POST: {self.request.POST}")
        return super().form_invalid(form)

    def render_to_response(self, context, **response_kwargs):
        """Renderizar usando el template correcto"""
        return super().render_to_response(context, **response_kwargs)


@method_decorator(login_required, name="dispatch")
class DocumentoDetailView(CountryLangTemplateMixin, DetailView):
    """Vista para ver detalles de un documento"""

    model = Documento
    context_object_name = "documento"
    base_template_name = "documentos/ver_documento_nuevo.html"

    def get_queryset(self):
        """Asegurar que solo se vean documentos de la empresa"""
        return Documento.objects.filter(empresa=self.request.user.empresa)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documento = self.object

        # Obtener líneas del documento
        repuestos = list(documento.lineas_repuesto.all().select_related("repuesto", "part"))
        servicios = list(documento.lineas_servicio.all().select_related("servicio", "service"))
        otros_servicios = list(documento.lineas_otro_servicio.all())

        # Calcular subtotales usando las propiedades subtotal de los modelos
        # Esto incluye descuentos y cantidades correctamente
        subtotal_repuestos = sum(
            Decimal(str(linea.subtotal)) if hasattr(linea, "subtotal") else Decimal("0.00")
            for linea in repuestos
        )
        subtotal_servicios = sum(
            Decimal(str(linea.subtotal)) if hasattr(linea, "subtotal") else Decimal("0.00")
            for linea in servicios
        )
        subtotal_otros_servicios = sum(
            Decimal(str(otro.subtotal)) if hasattr(otro, "subtotal") else Decimal("0.00")
            for otro in otros_servicios
        )

        # Debug logging
        print(
            f"DEBUG: DocumentoDetailView - Repuestos: {len(repuestos)}, Servicios: {len(servicios)}, Otros: {len(otros_servicios)}"
        )
        print(
            f"DEBUG: subtotal_repuestos: {subtotal_repuestos}, subtotal_servicios: {subtotal_servicios}, subtotal_otros: {subtotal_otros_servicios}"
        )

        subtotal = subtotal_repuestos + subtotal_servicios + subtotal_otros_servicios

        # Calcular IVA (19% solo sobre repuestos según la lógica de negocio)
        iva = subtotal_repuestos * Decimal("0.19")
        total = subtotal + iva

        print(f"DEBUG: subtotal: {subtotal}, iva: {iva}, total: {total}")

        context.update(
            {
                "lineas_repuesto": repuestos,
                "lineas_servicio": servicios,
                "lineas_otro_servicio": otros_servicios,
                "repuestos": repuestos,  # Mantener compatibilidad
                "servicios": servicios,  # Mantener compatibilidad
                "otros_servicios": otros_servicios,  # Mantener compatibilidad
                "subtotal_repuestos": subtotal_repuestos,
                "subtotal_servicios": subtotal_servicios,
                "subtotal_otros_servicios": subtotal_otros_servicios,
                "subtotal": subtotal,
                "iva": iva,
                "total": total,
            }
        )
        return context

    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)


@method_decorator(login_required, name="dispatch")
class DocumentoUpdateView(DocumentoLineItemsMixin, CountryLangTemplateMixin, UpdateView):
    """Vista para editar documentos"""

    model = Documento
    form_class = DocumentoForm
    base_template_name = "documentos/document_form.html"  # Usar el mismo template que CreateView

    def get_queryset(self):
        """Asegurar que solo se editen documentos de la empresa"""
        if not self.request.user.is_authenticated:
            return Documento.objects.none()
        
        # Obtener empresa de forma robusta
        empresa = getattr(self.request.user, "empresa", None)
        if not empresa:
            # Intentar obtener empresa desde el middleware
            empresa = getattr(self.request, "empresa", None)
        
        if not empresa:
            return Documento.objects.none()
        
        # Filtrar por empresa sin prefetch que pueda fallar
        # El prefetch se hará después en get_context_data si es necesario
        return Documento.objects.filter(empresa=empresa)

    def get_object(self, queryset=None):
        """Obtener el documento con mejor manejo de errores"""
        from django.shortcuts import get_object_or_404
        
        if queryset is None:
            queryset = self.get_queryset()
        
        pk = self.kwargs.get("pk")
        
        # Obtener empresa para verificación
        empresa_user = getattr(self.request.user, "empresa", None) or getattr(self.request, "empresa", None)
        
        # Intentar obtener del queryset filtrado
        try:
            documento = queryset.get(pk=pk)
            return documento
        except Documento.DoesNotExist:
            # Si no está en el queryset, verificar si existe y pertenece a la empresa
            if empresa_user:
                try:
                    documento = Documento.objects.get(pk=pk, empresa=empresa_user)
                    # Si llegamos aquí, el documento existe y pertenece a la empresa
                    # pero no está en el queryset - puede ser un problema de cache o evaluación
                    return documento
                except Documento.DoesNotExist:
                    # Verificar si existe pero pertenece a otra empresa
                    try:
                        documento = Documento.objects.get(pk=pk)
                        from django.contrib import messages
                        messages.error(
                            self.request,
                            f"El documento #{pk} no pertenece a tu empresa."
                        )
                    except Documento.DoesNotExist:
                        from django.contrib import messages
                        messages.error(
                            self.request,
                            f"El documento #{pk} no existe."
                        )
            else:
                from django.contrib import messages
                messages.error(
                    self.request,
                    "No tienes una empresa asociada."
                )
            
            from django.http import Http404
            raise Http404(f"No se encontró el documento #{pk}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Asegurar que tenemos el objeto documento
        documento = self.object or getattr(self, 'object', None)
        if not documento:
            # Si no está en self.object, intentar obtenerlo del pk
            pk = self.kwargs.get('pk')
            if pk:
                documento = self.get_object()
        
        if not documento:
            from django.http import Http404
            raise Http404("Documento no encontrado")
        
        empresa = getattr(self.request.user, "empresa", None) or getattr(self.request, "empresa", None)
        if not empresa:
            from django.http import Http404
            raise Http404("Empresa no encontrada")

        # Obtener líneas del documento para edición
        servicios = documento.lineas_servicio.all().select_related("servicio")
        repuestos = documento.lineas_repuesto.all().select_related("repuesto")
        otros_servicios = documento.lineas_otro_servicio.all()

        # Calcular subtotales
        subtotal_repuestos = sum(linea.precio_unitario * linea.cantidad for linea in repuestos)
        subtotal_servicios = sum(linea.precio_unitario * linea.cantidad for linea in servicios)
        subtotal_otros_servicios = sum(
            getattr(otro, "precio_cliente", Decimal("0.00")) for otro in otros_servicios
        )

        # Calcular totales
        subtotal = subtotal_repuestos + subtotal_servicios + subtotal_otros_servicios
        iva = subtotal * Decimal("0.19")
        total = subtotal + iva

        # Cargar mecánicos activos del taller
        mecanicos = Tecnico.objects.filter(empresa=empresa, activo=True)

        path = (self.request.path or "").lower()
        path_country = "CL"
        if path.startswith("/us/"):
            path_country = "US"
        elif path.startswith("/mx/"):
            path_country = "MX"
        elif path.startswith("/pe/"):
            path_country = "PE"
        elif path.startswith("/ve/"):
            path_country = "VE"
        elif path.startswith("/br/"):
            path_country = "BR"

        company_country = (
            getattr(self.request, "company_country", None)
            or getattr(empresa, "pais", None)
            or path_country
        )

        cliente = getattr(documento, "cliente", None)
        vehiculo = getattr(documento, "vehiculo", None)

        # Obtener ui_config de la empresa
        ui_config = {}
        try:
            from taller.configuracion.rubros_logic import get_ui_config
            config = getattr(empresa, "config", None)
            if config:
                ui_config = get_ui_config(config)
        except Exception:
            pass
        
        # Si no hay configuración, usar valores por defecto
        if not ui_config:
            ui_config = {
                "show_repuestos": True,
                "show_services": True,
                "show_otros_servicios": True,
                "show_kilometraje": True,
                "show_vehicle": True,
            }

        # Serializar datos para JavaScript
        repuestos_json = []
        for rep in repuestos:
            repuestos_json.append({
                "id": rep.id,
                "repuesto_id": rep.repuesto_id if rep.repuesto else None,
                "codigo": rep.codigo or "",
                "nombre": rep.nombre or "",
                "cantidad": float(rep.cantidad or 0),
                "precio": float(rep.precio_unitario or 0),
                "descuento": float(getattr(rep, "descuento", 0) or 0),
            })
        
        servicios_json = []
        for serv in servicios:
            servicios_json.append({
                "id": serv.id,
                "servicio_id": serv.servicio_id if serv.servicio else None,
                "nombre": serv.nombre or "",
                "cantidad": float(serv.cantidad or 0),
                "precio": float(serv.precio_unitario or 0),
                "descuento": float(getattr(serv, "descuento", 0) or 0),
            })
        
        otros_json = []
        for otro in otros_servicios:
            otros_json.append({
                "id": otro.id,
                "servicio_id": otro.servicio_id if otro.servicio else None,
                "nombre": otro.nombre or "",
                "empresa_ext": getattr(otro, "empresa_externa", "") or "",
                "precio_taller": float(getattr(otro, "costo_interno", 0) or 0),
                "precio": float(getattr(otro, "precio_cliente", 0) or 0),
            })

        context.update(
            {
                "documento": documento,
                "servicios": servicios,
                "repuestos": repuestos,
                "otros_servicios": otros_servicios,
                "repuestos_json": repuestos_json,
                "servicios_json": servicios_json,
                "otros_json": otros_json,
                "subtotal_repuestos": subtotal_repuestos,
                "subtotal_servicios": subtotal_servicios,
                "subtotal_otros_servicios": subtotal_otros_servicios,
                "subtotal": subtotal,
                "iva": iva,
                "total": total,
                "mecanicos": mecanicos,
                "tecnicos": mecanicos,  # Alias para compatibilidad con templates
                "es_edicion": True,
                "company_country": company_country,
                "empresa": empresa,  # Agregar empresa al contexto para que esté disponible en el template
                "ui_config": ui_config,
                "kilometraje": getattr(documento, "kilometraje_vehiculo", None) or getattr(documento, "kilometraje", None),
                "cliente_info": {
                    "id": getattr(cliente, "id", ""),
                    "nombre": str(cliente) if cliente else "",
                    "email": getattr(cliente, "email", "") if cliente else "",
                    "telefono": getattr(cliente, "telefono", "") if cliente else "",
                },
                "vehiculo_inicial_id": getattr(vehiculo, "id", "") or "",
            }
        )
        return context

    def get_success_url(self):
        """Redirigir a la vista del documento después de editarlo exitosamente."""
        return _reverse_with_request(self.request, "ver_documento", kwargs={"pk": self.object.pk})

    def get_form_kwargs(self):
        """Inyectar empresa/usuario en el formulario para aislar datos del tenant"""
        kwargs = super().get_form_kwargs()

        empresa_usuario = getattr(self.request.user, "empresa", None)
        empresa_documento = getattr(self.object, "empresa", None)
        empresa = empresa_documento or empresa_usuario

        kwargs["user"] = self.request.user
        kwargs["empresa"] = empresa

        if empresa and getattr(empresa, "pais", None):
            country = (empresa.pais or "CL").upper()
        else:
            country = "US" if self.request.path.startswith("/us/") else "CL"
        kwargs["country"] = country

        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        empresa = getattr(self.request.user, "empresa", None)
        cliente = getattr(form.instance, "cliente", None)

        if empresa and cliente:
            vehiculos_qs = (
                Vehiculo.objects.filter(empresa=empresa, cliente=cliente)
                .select_related("marca", "modelo")
                .order_by("patente", "vin", "id")
            )
            form.fields["vehiculo"].queryset = vehiculos_qs

            # Renderizar como select clásico para mostrar todas las opciones disponibles
            choices = [("", "---------")]
            for vehiculo in vehiculos_qs:
                if hasattr(vehiculo, "display_label"):
                    label = vehiculo.display_label()
                else:
                    partes = [
                        getattr(getattr(vehiculo, "marca", None), "nombre", ""),
                        getattr(getattr(vehiculo, "modelo", None), "nombre", ""),
                        getattr(vehiculo, "patente", "") or getattr(vehiculo, "placa", ""),
                    ]
                    label = " - ".join([p for p in partes if p]) or f"Vehículo #{vehiculo.pk}"
                choices.append((vehiculo.pk, label))

            attrs = {
                "class": "form-select w-full",
                "data-source": "form",
                "data-initial-vehicle": getattr(form.instance.vehiculo, "id", "") or "",
            }
            form.fields["vehiculo"].widget = forms.Select(attrs=attrs)
            form.fields["vehiculo"].widget.choices = choices

        return form

    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)

    def form_valid(self, form):
        response = super().form_valid(form)
        self.procesar_items_dinamicos(self.object, clear_existing=True)

        from django.contrib import messages

        messages.success(
            self.request,
            f"Documento {self.object.numero_documento} actualizado correctamente.",
        )
        return response


from taller.auth.decorators_role import RoleRequiredMixin


@method_decorator(login_required, name="dispatch")
class DocumentoDeleteView(CountryLangTemplateMixin, RoleRequiredMixin, DeleteView):
    """
    Vista para eliminar documentos.

    🔒 SOLO Owner y Admin pueden eliminar documentos.
    Un técnico o vendedor no debería poder borrar evidencia (facturas/OTs).
    """

    model = Documento
    base_template_name = "documentos/confirmar_eliminar.html"
    success_url = "/documentos/"
    allowed_roles = ["Owner", "Admin"]
    permission_denied_message = "Solo el dueño y administradores pueden eliminar documentos."

    def get_queryset(self):
        """🔒 MULTI-TENANT: Asegurar que solo se eliminen documentos de la empresa"""
        return Documento.objects.filter(empresa=self.request.user.empresa)

    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)
