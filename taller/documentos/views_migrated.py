"""
Vistas de documentos migradas para usar CountryLangTemplateMixin
Esto reemplaza las vistas FBV que están en views.py con plantillas hardcodeadas
"""

import re
from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
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
from taller.models import Documento, Empresa, Tecnico
from taller.utils.empresa import get_or_create_empresa
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


def _total_from_documento_lines(documento):
    """
    Calcula el total del documento desde las líneas prefetched (repuestos, servicios, otros).
    IVA solo sobre repuestos para CL (19%). Retorna (total, neto_rep, neto_serv, neto_otros).
    """

    def _line_subtotal(line, qty_attr="cantidad", price_attr="precio_unitario"):
        q = getattr(line, qty_attr, 1) or 1
        p = getattr(line, price_attr, None) or Decimal("0")
        try:
            return Decimal(str(q)) * Decimal(str(p))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal("0")

    rep = sum(
        (_line_subtotal(l, "cantidad", "precio_unitario") for l in documento.lineas_repuesto.all()),
        Decimal("0"),
    )
    serv = sum(
        (_line_subtotal(l, "cantidad", "precio_unitario") for l in documento.lineas_servicio.all()),
        Decimal("0"),
    )
    otros = sum(
        (
            _line_subtotal(l, "cantidad", "precio_cliente")
            for l in documento.lineas_otro_servicio.all()
        ),
        Decimal("0"),
    )
    pais = getattr(getattr(documento, "empresa", None), "pais", "CL") or "CL"
    iva = Decimal("0")
    if str(pais).upper() == "CL" and rep > 0:
        iva = (rep * Decimal("0.19")).quantize(Decimal("0.01"))
    total = rep + serv + otros + iva
    return (total, rep, serv, otros)


def build_document_list_queryset(empresa, request=None):
    """
    Construye el queryset de documentos para listado: filtros opcionales (si request)
    y anotaciones de totales (rep_sum, serv_sum, total_display, etc.) para que
    los totales se muestren correctamente aunque el campo total en BD sea 0.
    """
    base_queryset = (
        Documento.objects.filter(empresa=empresa)
        .select_related("cliente", "vehiculo", "tecnico_responsable")
        .prefetch_related(
            "lineas_repuesto__repuesto",
            "lineas_servicio__servicio",
            "lineas_otro_servicio",
        )
    )
    if request:
        cliente_search = (request.GET.get("cliente") or "").strip()
        if cliente_search:
            base_queryset = base_queryset.filter(
                Q(cliente__nombre__icontains=cliente_search)
                | Q(cliente__apellido__icontains=cliente_search)
                | Q(cliente__email__icontains=cliente_search)
            )
        vehiculo_search = (request.GET.get("vehiculo") or "").strip()
        if vehiculo_search:
            base_queryset = base_queryset.filter(
                Q(vehiculo__patente__icontains=vehiculo_search)
                | Q(vehiculo__marca__nombre__icontains=vehiculo_search)
                | Q(vehiculo__modelo__nombre__icontains=vehiculo_search)
            )
        estado = (request.GET.get("estado") or "").strip()
        if estado:
            base_queryset = base_queryset.filter(estado=estado.upper())
        tipo = (request.GET.get("tipo") or "").strip()
        if tipo:
            base_queryset = base_queryset.filter(tipo=tipo.upper())
        fecha_desde = (request.GET.get("desde") or "").strip()
        if fecha_desde:
            try:
                from datetime import datetime

                fecha_desde_obj = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
                base_queryset = base_queryset.filter(fecha_emision__gte=fecha_desde_obj)
            except ValueError:
                pass
        fecha_hasta = (request.GET.get("hasta") or "").strip()
        if fecha_hasta:
            try:
                from datetime import datetime

                fecha_hasta_obj = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
                base_queryset = base_queryset.filter(fecha_emision__lte=fecha_hasta_obj)
            except ValueError:
                pass
        numero = (request.GET.get("numero") or "").strip()
        if numero:
            base_queryset = base_queryset.filter(numero__icontains=numero)

    decimal_zero = Value(
        Decimal("0"),
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )
    return (
        base_queryset.annotate(
            rep_sum=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("lineas_repuesto__cantidad") * F("lineas_repuesto__precio_unitario"),
                        output_field=DecimalField(max_digits=14, decimal_places=2),
                    )
                ),
                decimal_zero,
            ),
            serv_sum=Coalesce(
                Sum(
                    ExpressionWrapper(
                        F("lineas_servicio__cantidad") * F("lineas_servicio__precio_unitario"),
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
            total_computed=ExpressionWrapper(
                F("rep_sum") + F("serv_sum") + F("otros_sum") + F("iva_calc"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        )
        .annotate(
            total_display=Case(
                When(legacy_total_general__isnull=True, then=F("total_computed")),
                When(legacy_total_general=0, then=F("total_computed")),
                default=F("legacy_total_general"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            ),
        )
        .order_by("-fecha_emision", "-id")
    )


def enrich_documentos_with_totals(documentos):
    """
    Rellena total, neto_repuestos, neto_servicios, neto_otros_servicios y tax_amount
    en cada documento a partir de anotaciones (rep_sum, serv_sum, total_display, etc.)
    o, si faltan, desde líneas prefetched. Así se evita mostrar $0 cuando el total
    en BD no está actualizado.
    """
    for documento in documentos:
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

        neto_rep = getattr(documento, "neto_repuestos", Decimal("0")) or Decimal("0")
        neto_serv = getattr(documento, "neto_servicios", Decimal("0")) or Decimal("0")
        neto_otros = getattr(documento, "neto_otros_servicios", Decimal("0")) or Decimal("0")
        iva = getattr(documento, "tax_amount", Decimal("0")) or Decimal("0")
        computed_total = neto_rep + neto_serv + neto_otros + iva

        if (
            hasattr(documento, "total_display")
            and documento.total_display is not None
            and documento.total_display > 0
        ):
            documento.total = documento.total_display
        elif (
            getattr(documento, "legacy_total_general", None) and documento.legacy_total_general > 0
        ):
            documento.total = documento.legacy_total_general
        else:
            documento.total = computed_total

        if (documento.total is None or documento.total <= 0) and hasattr(
            documento, "lineas_repuesto"
        ):
            total_from_lines, neto_rep, neto_serv, neto_otros = _total_from_documento_lines(
                documento
            )
            if total_from_lines > 0:
                documento.total = total_from_lines
                documento.neto_repuestos = neto_rep
                documento.neto_servicios = neto_serv
                documento.neto_otros_servicios = neto_otros

        if documento.total is None:
            documento.total = Decimal("0")


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
    REPUESTO_FIELDS = (
        "codigo",
        "nombre",
        "cantidad",
        "precio_unitario",
        "precio_compra",
        "source_type",
        "customer_part_description",
        "customer_part_notes",
    )
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
            source_type = (data.get("source_type") or "IN_STOCK").upper()
            if source_type not in ("CUSTOMER_SUPPLIED", "IN_STOCK", "SOURCED"):
                source_type = "IN_STOCK"
            precio_unitario = (
                Decimal("0")
                if source_type == "CUSTOMER_SUPPLIED"
                else _to_decimal(data.get("precio_unitario"), Decimal("0"))
            )
            linea = LineaRepuesto(
                documento=documento,
                codigo=codigo or nombre,
                nombre=nombre or codigo,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                source_type=source_type,
                customer_part_description=(data.get("customer_part_description") or "").strip()
                or None,
                customer_part_notes=(data.get("customer_part_notes") or "").strip() or None,
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
class DocumentoListView(LoginRequiredMixin, CountryLangTemplateMixin, ListView):
    """Vista para listar documentos de la empresa"""

    model = Documento
    context_object_name = "documentos"
    base_template_name = "documentos/lista_documentos.html"
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        """Evitar 500: empresa + captura de cualquier excepción en la vista."""
        import logging
        from django.core.exceptions import PermissionDenied
        from django.http import HttpResponseRedirect
        from django.urls import reverse

        if request.user.is_authenticated:
            try:
                get_or_create_empresa(request)
            except PermissionDenied:
                raise
            except Exception as e:
                logging.getLogger(__name__).exception(
                    "DocumentoListView dispatch get_or_create_empresa: %s", e
                )
                return HttpResponseRedirect(reverse("admin:index"))
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logging.getLogger(__name__).exception("DocumentoListView unhandled: %s", e)
            try:
                return HttpResponseRedirect(reverse("admin:index"))
            except Exception:
                return HttpResponseRedirect("/")

    def get_template_names(self):
        """Template para lista de documentos con fallbacks (evitar 500 si falta taller/us/en/...)."""
        if self.request.path.startswith("/us/"):
            # Orden: específico US/EN → común; en producción puede existir us/en/ o solo taller/common/
            return [
                "us/en/documentos/lista_documentos.html",
                "taller/us/en/documentos/lista_documentos.html",
                "taller/common/documentos/lista_documentos.html",
                "documentos/lista_documentos.html",
            ]
        return super().get_template_names()

    def get_queryset(self):
        """Filtrar documentos por empresa del usuario con filtros funcionales"""
        try:
            empresa = get_or_create_empresa(self.request)
        except Exception:
            return Documento.objects.none()
        try:
            return build_document_list_queryset(empresa, self.request)
        except Exception as e:
            import logging

            logging.getLogger(__name__).exception(
                "DocumentoListView build_document_list_queryset: %s", e
            )
            return Documento.objects.filter(empresa=empresa).order_by("-fecha_emision", "-id")[:100]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            empresa = get_or_create_empresa(self.request)
        except Exception:
            empresa = None
        if empresa is None:
            context["empresa"] = None
            context["country"] = "cl"
            context["estadisticas"] = {
                "total": 0,
                "emitidos": 0,
                "borradores": 0,
                "anulados": 0,
                "hoy": 0,
                "ultimos_30_dias": 0,
                "pendientes_pago": 0,
                "presupuestos_pendientes": 0,
                "ots_sin_cerrar": 0,
                "total_monto": Decimal("0"),
            }
            context["documentos_pendientes"] = 0
            context["documentos_proceso"] = 0
            context["documentos_completados"] = 0
            context["filtros_activos"] = {}
            return context

        context["country"] = getattr(empresa, "pais", "cl").lower()
        context["empresa"] = empresa

        documentos = context.get("documentos", [])
        try:
            enrich_documentos_with_totals(documentos)
        except Exception as e:
            import logging

            logging.getLogger(__name__).exception(
                "DocumentoListView enrich_documentos_with_totals: %s", e
            )

        # === KPIs Y ESTADÍSTICAS CALCULADAS ===
        from datetime import date, timedelta

        hoy = date.today()
        hace_30_dias = hoy - timedelta(days=30)
        default_estadisticas = {
            "total": 0,
            "emitidos": 0,
            "borradores": 0,
            "anulados": 0,
            "hoy": 0,
            "ultimos_30_dias": 0,
            "pendientes_pago": 0,
            "presupuestos_pendientes": 0,
            "ots_sin_cerrar": 0,
            "total_monto": Decimal("0"),
        }
        cliente_search = self.request.GET.get("cliente", "").strip()
        vehiculo_search = self.request.GET.get("vehiculo", "").strip()
        estado = self.request.GET.get("estado", "").strip()
        tipo = self.request.GET.get("tipo", "").strip()
        fecha_desde = self.request.GET.get("desde", "").strip()
        fecha_hasta = self.request.GET.get("hasta", "").strip()
        numero = self.request.GET.get("numero", "").strip()

        try:
            stats_qs = Documento.objects.filter(empresa=empresa)
            if cliente_search:
                stats_qs = stats_qs.filter(
                    Q(cliente__nombre__icontains=cliente_search)
                    | Q(cliente__apellido__icontains=cliente_search)
                    | Q(cliente__email__icontains=cliente_search)
                )
            if vehiculo_search:
                stats_qs = stats_qs.filter(
                    Q(vehiculo__patente__icontains=vehiculo_search)
                    | Q(vehiculo__marca__nombre__icontains=vehiculo_search)
                    | Q(vehiculo__modelo__nombre__icontains=vehiculo_search)
                )
            if estado:
                stats_qs = stats_qs.filter(estado=estado.upper())
            if tipo:
                stats_qs = stats_qs.filter(tipo=tipo.upper())
            if fecha_desde:
                try:
                    from datetime import datetime

                    fecha_desde_obj = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
                    stats_qs = stats_qs.filter(fecha_emision__gte=fecha_desde_obj)
                except ValueError:
                    pass
            if fecha_hasta:
                try:
                    from datetime import datetime

                    fecha_hasta_obj = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
                    stats_qs = stats_qs.filter(fecha_emision__lte=fecha_hasta_obj)
                except ValueError:
                    pass
            if numero:
                stats_qs = stats_qs.filter(numero__icontains=numero)

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
            total_calculado = stats_qs.aggregate(
                sum_rep=Sum("neto_repuestos"),
                sum_serv=Sum("neto_servicios"),
                sum_otros=Sum("neto_otros_servicios"),
                sum_tax=Sum("tax_amount"),
            )
            estadisticas["total_monto"] = (
                (total_calculado["sum_rep"] or Decimal("0"))
                + (total_calculado["sum_serv"] or Decimal("0"))
                + (total_calculado["sum_otros"] or Decimal("0"))
                + (total_calculado["sum_tax"] or Decimal("0"))
            )
        except Exception as e:
            import logging

            logging.getLogger(__name__).exception("DocumentoListView get_context_data stats: %s", e)
            estadisticas = default_estadisticas.copy()

        context["estadisticas"] = estadisticas
        context["documentos_pendientes"] = estadisticas.get("borradores", 0)
        context["documentos_proceso"] = estadisticas.get("emitidos", 0)
        context["documentos_completados"] = estadisticas.get("emitidos", 0)
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
        from django.template import TemplateDoesNotExist
        from django.http import HttpResponse

        try:
            return self.render_country_lang(self.request, context)
        except TemplateDoesNotExist as e:
            import logging

            logging.getLogger(__name__).warning("DocumentoListView template missing: %s", e)
            html = (
                "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Documents</title></head>"
                "<body><h1>Documents</h1><p>Document list is loading.</p>"
                "<p><a href='/us/'>Back to dashboard</a></p></body></html>"
            )
            return HttpResponse(html, content_type="text/html; charset=utf-8")
        except Exception as e:
            import logging

            logging.getLogger(__name__).exception("DocumentoListView render_to_response: %s", e)
            html = (
                "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Error</title></head>"
                "<body><h1>Error loading page</h1><p>Please try again or contact support.</p>"
                "<p><a href='/us/'>Back to dashboard</a></p></body></html>"
            )
            return HttpResponse(html, content_type="text/html; charset=utf-8")


class DocumentoCreateView(
    LoginRequiredMixin, DocumentoLineItemsMixin, CountryLangTemplateMixin, CreateView
):
    """Vista para crear documentos."""

    redirect_field_name = "next"

    def get_login_url(self):
        path = (self.request.path or "/").strip("/")
        parts = [p for p in path.split("/") if p]
        country = parts[0] if parts else "cl"
        lang = "es"
        if len(parts) > 1 and parts[1] in ("es", "en"):
            lang = parts[1]
        elif country == "us":
            lang = "en"
        return f"/{country}/accounts/login/"

    model = Documento
    form_class = DocumentoForm
    base_template_name = "documentos/document_form.html"

    def dispatch(self, request, *args, **kwargs):
        """Asegurar empresa y capturar cualquier excepción para evitar 500."""
        import logging
        from django.core.exceptions import PermissionDenied
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        from django.contrib import messages

        if request.user.is_authenticated:
            try:
                get_or_create_empresa(request)
            except PermissionDenied:
                raise
            except Exception as e:
                logging.getLogger(__name__).exception(
                    "DocumentoCreateView dispatch get_or_create_empresa: %s", e
                )
                messages.error(
                    request,
                    "No se pudo cargar la empresa. Revisa tu cuenta o contacta al administrador.",
                )
                return HttpResponseRedirect(reverse("admin:index"))
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logging.getLogger(__name__).exception("DocumentoCreateView unhandled: %s", e)
            messages.error(
                request,
                "Error al cargar el formulario. Intenta de nuevo o contacta al administrador.",
            )
            try:
                return HttpResponseRedirect(reverse("admin:index"))
            except Exception:
                return HttpResponseRedirect("/")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = get_or_create_empresa(self.request)

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

        # Prefill cliente desde GET para que el template muestre seleccionado
        prefill_cliente_id = (self.request.GET.get("prefill_cliente") or "").strip()
        prefill_cliente_nombre = (self.request.GET.get("prefill_cliente_nombre") or "").strip()
        prefill_cliente_email = (self.request.GET.get("prefill_cliente_email") or "").strip()
        prefill_cliente_telefono = (self.request.GET.get("prefill_cliente_telefono") or "").strip()

        # Prefill vehículo desde GET (para Select2 / inyección de option en template)
        prefill_vehiculo_id = (
            (self.request.GET.get("prefill_vehiculo") or "")
            or (self.request.GET.get("new_vehiculo_id") or "")
        ).strip()
        prefill_vehiculo_label = ""
        if prefill_vehiculo_id and empresa:
            vehiculo_obj = Vehiculo.objects.filter(empresa=empresa, pk=prefill_vehiculo_id).first()
            if vehiculo_obj:
                prefill_vehiculo_label = str(vehiculo_obj)

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
                "prefill_cliente_id": prefill_cliente_id,
                "prefill_cliente_nombre": prefill_cliente_nombre,
                "prefill_cliente_email": prefill_cliente_email,
                "prefill_cliente_telefono": prefill_cliente_telefono,
                "prefill_vehiculo_id": prefill_vehiculo_id,
                "prefill_vehiculo_label": prefill_vehiculo_label,
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
                try:
                    label = (
                        vehiculo.display_label()
                        if hasattr(vehiculo, "display_label")
                        else str(vehiculo)
                    )
                except Exception:
                    label = str(vehiculo)
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

            # No filtrar por names__language: muchos servicios solo tienen campo nombre (sin ServicioName),
            # y get_label(language) ya hace fallback a self.nombre
            servicios_qs = (
                Servicio.objects.filter(empresa=empresa, activo=True)
                .select_related("categoria", "subcategoria")
                .prefetch_related("names", "categoria__names", "subcategoria__names")
                .order_by("categoria__orden", "subcategoria__orden", "nombre")[:50]
            )
            for servicio in servicios_qs:
                try:
                    nombre = (
                        servicio.get_label(language)
                        if hasattr(servicio, "get_label")
                        else getattr(servicio, "nombre", str(servicio))
                    )
                    cat_label = (
                        servicio.categoria.get_label(language)
                        if servicio.categoria and hasattr(servicio.categoria, "get_label")
                        else ""
                    ) or (getattr(servicio.categoria, "nombre", "") if servicio.categoria else "")
                    sub_label = (
                        servicio.subcategoria.get_label(language)
                        if servicio.subcategoria and hasattr(servicio.subcategoria, "get_label")
                        else ""
                    ) or (
                        getattr(servicio.subcategoria, "nombre", "")
                        if servicio.subcategoria
                        else ""
                    )
                    servicios_prefetch.append(
                        {
                            "id": servicio.id,
                            "nombre": nombre,
                            "categoria": cat_label,
                            "categoria_code": servicio.categoria.code if servicio.categoria else "",
                            "subcategoria": sub_label,
                            "subcategoria_code": (
                                servicio.subcategoria.code if servicio.subcategoria else ""
                            ),
                            "precio": 0.0,
                            "precio_sugerido": 0.0,
                            "precio_cliente": 0.0,
                        }
                    )
                except Exception:
                    servicios_prefetch.append(
                        {
                            "id": getattr(servicio, "id", 0),
                            "nombre": getattr(servicio, "nombre", str(servicio)),
                            "categoria": "",
                            "categoria_code": "",
                            "subcategoria": "",
                            "subcategoria_code": "",
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
                try:
                    cat_ext = (
                        externo.categoria.get_label(language)
                        if (externo.categoria and hasattr(externo.categoria, "get_label"))
                        else ""
                    ) or (getattr(externo.categoria, "nombre", "") if externo.categoria else "")
                    sub_ext = (
                        externo.subcategoria.get_label(language)
                        if externo.subcategoria and hasattr(externo.subcategoria, "get_label")
                        else ""
                    ) or (
                        getattr(externo.subcategoria, "nombre", "") if externo.subcategoria else ""
                    )
                    otros_servicios_prefetch.append(
                        {
                            "id": externo.id,
                            "nombre": getattr(externo, "nombre", ""),
                            "empresa": getattr(externo, "empresa_externa", ""),
                            "empresa_ext": getattr(externo, "empresa_externa", ""),
                            "categoria": cat_ext,
                            "subcategoria": sub_ext,
                            "precio_taller": float(
                                getattr(externo, "costo_taller", None) or Decimal("0")
                            ),
                            "precio_cliente": float(
                                getattr(externo, "precio_cliente", None) or Decimal("0")
                            ),
                        }
                    )
                except Exception:
                    otros_servicios_prefetch.append(
                        {
                            "id": getattr(externo, "id", 0),
                            "nombre": getattr(externo, "nombre", ""),
                            "empresa": "",
                            "empresa_ext": "",
                            "categoria": "",
                            "subcategoria": "",
                            "precio_taller": 0.0,
                            "precio_cliente": 0.0,
                        }
                    )

        # Obtener ui_config de la empresa
        ui_config = {}
        config = getattr(empresa, "config", None)
        if config is None:
            from taller.models.configuracion import ConfiguracionEmpresa

            config = ConfiguracionEmpresa.objects.filter(empresa=empresa).first()
        try:
            from taller.configuracion.rubros_logic import get_ui_config

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

        # USA: Tax en Totals — ConfiguracionEmpresa.sales_tax_rate o fallback CompanySettings.tax_rate (Impuestos y Finanzas)
        rate = 0
        if country_code == "US":
            if config:
                try:
                    val = getattr(config, "sales_tax_rate", None)
                    rate = float(val) if val is not None else 0
                except (TypeError, ValueError):
                    rate = 0
            if rate == 0 and self.request.user.is_authenticated:
                try:
                    from taller.models.company_settings import CompanySettings

                    cs = CompanySettings.objects.filter(user=self.request.user).first()
                    if cs and getattr(cs, "tax_rate", None) is not None:
                        rate = float(cs.tax_rate)
                except (TypeError, ValueError, ImportError):
                    pass
            ui_config.setdefault("tax_lines", []).append(
                {
                    "id": "sales_tax",
                    "label": "Tax",
                    "rate": rate,
                    "applies_to": "all",
                }
            )
        if not ui_config.get("tax_lines"):
            ui_config["tax_lines"] = []
        ui_config.setdefault("currency_symbol", "$" if country_code == "US" else "$")

        # Tasa para data-sales-tax-rate en template (mismo valor que tax_lines para US)
        sales_tax_rate_ctx = float(rate) if country_code == "US" else 0

        # Base URL absoluta del app documentos (siempre .../documentos/ para que las APIs resuelvan)
        path = (self.request.path or "").strip().rstrip("/")
        if "documentos" in path:
            idx = path.find("documentos") + len("documentos")
            doc_base = path[:idx] + "/"
        else:
            # Form puede estar en /us/form/ o /cl/form/; la API está en /us/documentos/ o /cl/documentos/
            parts = path.strip("/").split("/")
            prefix = parts[0] if parts else ""
            doc_base = "/" + prefix + "/documentos/" if prefix else "/documentos/"
        document_api_base = (
            self.request.build_absolute_uri(doc_base) if doc_base.startswith("/") else doc_base
        )

        context.update(
            {
                "clientes_prefetch": clientes_prefetch,
                "vehiculos_prefetch": vehiculos_prefetch,
                "repuestos_prefetch": repuestos_prefetch,
                "servicios_prefetch": servicios_prefetch,
                "otros_servicios_prefetch": otros_servicios_prefetch,
                "ui_config": ui_config,
                "sales_tax_rate": sales_tax_rate_ctx,
                "document_api_base": document_api_base,
            }
        )
        return context

    def get_initial(self):
        """Número inicial por tipo, fecha hoy al crear, y prefill de cliente desde request.GET."""
        initial = super().get_initial()
        from django.utils import timezone

        initial["fecha_emision"] = timezone.now().date()
        empresa = getattr(self.request.user, "empresa", None)
        if empresa:
            tipo = self.request.GET.get("tipo") or "OT"
            initial["numero"] = Documento.get_next_number(empresa, tipo=tipo)
            # Prefill cliente desde ?prefill_cliente=id
            prefill_cliente = (self.request.GET.get("prefill_cliente") or "").strip()
            if prefill_cliente:
                try:
                    cliente = Cliente.objects.filter(empresa=empresa, pk=prefill_cliente).first()
                    if cliente:
                        initial["cliente"] = cliente
                except (ValueError, TypeError):
                    pass

            # Prefill vehículo desde ?prefill_vehiculo=id (o legacy ?new_vehiculo_id=id)
            prefill_vehiculo = (
                (self.request.GET.get("prefill_vehiculo") or "")
                or (self.request.GET.get("new_vehiculo_id") or "")
            ).strip()
            if prefill_vehiculo:
                try:
                    vehiculo = Vehiculo.objects.filter(empresa=empresa, pk=prefill_vehiculo).first()
                    if vehiculo:
                        initial["vehiculo"] = vehiculo
                        # Si viene cliente vacío, inferir del vehículo
                        if not initial.get("cliente") and getattr(vehiculo, "cliente_id", None):
                            initial["cliente"] = vehiculo.cliente
                except (ValueError, TypeError):
                    pass
        return initial

    def get_form_kwargs(self):
        """Obtener argumentos para el formulario"""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["empresa"] = getattr(self.request.user, "empresa", None)
        kwargs["country"] = "US" if self.request.path.startswith("/us/") else "CL"
        kwargs["request"] = self.request
        return kwargs

    def get_success_url(self):
        """Redirigir a la lista de documentos respetando el prefijo país/idioma."""
        return _reverse_with_request(self.request, "lista_documentos")

    def form_valid(self, form):
        form.instance.empresa = get_or_create_empresa(self.request)
        ctx = self.request.POST.get("context", "workshop")
        if ctx in ("workshop", "parts", "mixed"):
            form.instance.context = ctx
        if ctx == "parts":
            form.instance.vehiculo = None
            form.instance.kilometraje = None

        # Número: si viene vacío desde POST (JS falló o no envió), generar en backend
        numero = (
            form.cleaned_data.get("numero")
            or self.request.POST.get("numero_documento")
            or self.request.POST.get("numero")
            or ""
        )
        if not (numero and str(numero).strip()):
            form.instance.numero = ""
            # save() del modelo generará el número con generar_numero_documento()
        else:
            form.instance.numero = str(numero).strip()

        # Log real del POST: qué "names" están llegando (diagnóstico)
        import logging

        logger = logging.getLogger("egarage.docs")
        keys = sorted(list(self.request.POST.keys()))
        logger.warning("DOC CREATE POST KEYS (%s): %s", len(keys), keys[:400])
        sample_keys = keys[:60]
        logger.warning(
            "DOC CREATE POST SAMPLE: %s", {k: self.request.POST.get(k) for k in sample_keys}
        )
        array_like = [k for k in keys if k.endswith("[]")]
        logger.warning("DOC CREATE POST ARRAY KEYS (%s): %s", len(array_like), array_like[:200])

        # Guardar el documento primero (DocumentoForm.save ya llama _process_json_data
        # que crea líneas desde repuestos_json, servicios_json, otros_json)
        response = super().form_valid(form)

        # NO llamar procesar_items_dinamicos: espera campos rep-0-codigo, serv-0-nombre, etc.
        # pero el template document_form.html envía JSON en hidden. Llamarlo borraría las líneas
        # recién creadas y no las reemplazaría → documento.total=0. DocumentoForm ya lo maneja.

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

        # Obtener memoria y evidencias
        from taller.models.memoria_seguimiento import (
            EvidenciaDocumento,
            NotaInterna,
            EtiquetaAsignacion,
            SeguimientoPublico,
        )
        from taller.auth.decorators_role import is_staff_member

        es_staff = is_staff_member(self.request.user)

        # Obtener notas (filtrar por solo_staff si es técnico)
        if es_staff:
            notas = NotaInterna.objects.filter(documento=documento).order_by("-created_at")
        else:
            notas = NotaInterna.objects.filter(documento=documento, solo_staff=False).order_by(
                "-created_at"
            )

        # Obtener etiquetas asignadas (filtrar por solo_staff si es técnico)
        if es_staff:
            etiquetas_asignadas = EtiquetaAsignacion.objects.filter(
                documento=documento
            ).select_related("etiqueta")
        else:
            etiquetas_asignadas = EtiquetaAsignacion.objects.filter(
                documento=documento, etiqueta__solo_staff=False
            ).select_related("etiqueta")

        # Obtener evidencias
        evidencias = EvidenciaDocumento.objects.filter(documento=documento).order_by("-created_at")
        fotos_count = evidencias.filter(tipo="FOTO").count()
        videos_count = evidencias.filter(tipo="VIDEO").count()

        # Obtener seguimiento público si existe
        seguimiento_publico = getattr(documento, "seguimiento_publico", None)

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
                # Memoria y evidencias
                "notas": notas,
                "etiquetas_asignadas": etiquetas_asignadas,
                "evidencias": evidencias,
                "fotos_count": fotos_count,
                "videos_count": videos_count,
                "puede_agregar_foto": fotos_count < 4,
                "puede_agregar_video": videos_count < 1,
                "seguimiento_publico": seguimiento_publico,
                "es_staff": es_staff,
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
        empresa_user = getattr(self.request.user, "empresa", None) or getattr(
            self.request, "empresa", None
        )

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
                            self.request, f"El documento #{pk} no pertenece a tu empresa."
                        )
                    except Documento.DoesNotExist:
                        from django.contrib import messages

                        messages.error(self.request, f"El documento #{pk} no existe.")
            else:
                from django.contrib import messages

                messages.error(self.request, "No tienes una empresa asociada.")

            from django.http import Http404

            raise Http404(f"No se encontró el documento #{pk}")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Asegurar que tenemos el objeto documento
        documento = self.object or getattr(self, "object", None)
        if not documento:
            # Si no está en self.object, intentar obtenerlo del pk
            pk = self.kwargs.get("pk")
            if pk:
                documento = self.get_object()

        if not documento:
            from django.http import Http404

            raise Http404("Documento no encontrado")

        empresa = getattr(self.request.user, "empresa", None) or getattr(
            self.request, "empresa", None
        )
        if not empresa:
            from django.http import Http404

            raise Http404("Empresa no encontrada")

        # Obtener líneas del documento para edición
        servicios = documento.lineas_servicio.all().select_related("servicio")
        repuestos = documento.lineas_repuesto.all().select_related("repuesto")
        otros_servicios = list(documento.lineas_otro_servicio.all())

        # Calcular subtotales (evitar None en precio/cantidad)
        def _safe_mul(precio, cantidad):
            p = precio if precio is not None else Decimal("0")
            c = cantidad if cantidad is not None else 0
            return (Decimal(str(p)) * c) if c else Decimal("0")

        subtotal_repuestos = sum(
            _safe_mul(linea.precio_unitario, linea.cantidad) for linea in repuestos
        )
        subtotal_servicios = sum(
            _safe_mul(linea.precio_unitario, linea.cantidad) for linea in servicios
        )
        subtotal_otros_servicios = sum(
            Decimal(str(getattr(otro, "precio_cliente", None) or 0)) for otro in otros_servicios
        )

        # Calcular totales: preferir los guardados en el documento (correctos por país)
        subtotal = subtotal_repuestos + subtotal_servicios + subtotal_otros_servicios
        iva = getattr(documento, "tax_amount", None)
        if iva is None:
            iva = subtotal * Decimal("0.19")
        iva = Decimal(str(iva)) if iva is not None else Decimal("0")
        total = getattr(documento, "total", None)
        if total is None or total == 0:
            total = subtotal + iva
        total = Decimal(str(total)) if total is not None else (subtotal + iva)

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
        config = getattr(empresa, "config", None)
        if config is None:
            from taller.models.configuracion import ConfiguracionEmpresa

            config = ConfiguracionEmpresa.objects.filter(empresa=empresa).first()
        try:
            from taller.configuracion.rubros_logic import get_ui_config

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

        country_code = str(company_country or "CL").upper()
        rate = 0
        if country_code == "US":
            if config:
                try:
                    val = getattr(config, "sales_tax_rate", None)
                    rate = float(val) if val is not None else 0
                except (TypeError, ValueError):
                    rate = 0
            if rate == 0 and self.request.user.is_authenticated:
                try:
                    from taller.models.company_settings import CompanySettings

                    cs = CompanySettings.objects.filter(user=self.request.user).first()
                    if cs and getattr(cs, "tax_rate", None) is not None:
                        rate = float(cs.tax_rate)
                except (TypeError, ValueError, ImportError):
                    pass
            ui_config.setdefault("tax_lines", []).append(
                {
                    "id": "sales_tax",
                    "label": "Tax",
                    "rate": rate,
                    "applies_to": "all",
                }
            )
        if not ui_config.get("tax_lines"):
            ui_config["tax_lines"] = []
        ui_config.setdefault("currency_symbol", "$" if country_code == "US" else "$")

        # Serializar datos para JavaScript (valores numéricos seguros)
        def _f(v):
            try:
                return float(v) if v is not None else 0.0
            except (TypeError, ValueError):
                return 0.0

        repuestos_json = []
        for rep in repuestos:
            repuestos_json.append(
                {
                    "id": rep.id,
                    "repuesto_id": rep.repuesto_id if rep.repuesto else None,
                    "codigo": (rep.codigo or "").strip(),
                    "nombre": (rep.nombre or "").strip(),
                    "cantidad": _f(rep.cantidad),
                    "precio": _f(rep.precio_unitario),
                    "descuento": _f(getattr(rep, "descuento", 0)),
                }
            )

        servicios_json = []
        for serv in servicios:
            servicios_json.append(
                {
                    "id": serv.id,
                    "servicio_id": serv.servicio_id if serv.servicio else None,
                    "nombre": (serv.nombre or "").strip(),
                    "cantidad": _f(serv.cantidad),
                    "precio": _f(serv.precio_unitario),
                    "descuento": _f(getattr(serv, "descuento", 0)),
                }
            )

        otros_json = []
        for otro in otros_servicios:
            otros_json.append(
                {
                    "id": otro.id,
                    "servicio_id": getattr(otro, "servicio_id", None),
                    "nombre": (getattr(otro, "nombre", None) or "").strip(),
                    "empresa_ext": (getattr(otro, "empresa_externa", None) or "").strip(),
                    "precio_taller": _f(getattr(otro, "costo_interno", 0)),
                    "precio": _f(getattr(otro, "precio_cliente", 0)),
                }
            )

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
                "sales_tax_rate": float(rate) if country_code == "US" else 0,
                "total": total,
                "mecanicos": mecanicos,
                "tecnicos": mecanicos,  # Alias para compatibilidad con templates
                "es_edicion": True,
                "company_country": company_country,
                "empresa": empresa,  # Agregar empresa al contexto para que esté disponible en el template
                "ui_config": ui_config,
                "kilometraje": getattr(documento, "kilometraje_vehiculo", None)
                or getattr(documento, "kilometraje", None),
                "cliente_info": {
                    "id": getattr(cliente, "id", ""),
                    "nombre": str(cliente) if cliente else "",
                    "email": getattr(cliente, "email", "") if cliente else "",
                    "telefono": getattr(cliente, "telefono", "") if cliente else "",
                },
                "vehiculo_inicial_id": getattr(vehiculo, "id", "") or "",
                "prefill_cliente_id": "",
                "prefill_cliente_nombre": "",
                "prefill_cliente_email": "",
                "prefill_cliente_telefono": "",
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
        ctx = self.request.POST.get("context", "workshop")
        if ctx == "parts":
            form.instance.vehiculo = None
            form.instance.kilometraje = None
        # DocumentoForm.save() ya llama _process_json_data para líneas (repuestos_json, etc.)
        # NO procesar_items_dinamicos: el template usa JSON, no rep-0-codigo. Ver DocumentoCreateView.
        response = super().form_valid(form)

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
