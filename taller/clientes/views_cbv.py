from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Count, Q
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.views import TenantViewMixin
from taller.common.mixins.context_return import ContextReturnCreateMixin
from taller.mixins import CountryLangTemplateMixin
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.templatetags.country_url import reverse_country_url
from taller.utils.empresa import get_user_empresa_safe

STATE_CITY_COUNTRIES = {"US", "BR", "VE", "PE", "MX", "CO", "EC"}


def _route_country(request, fallback=None):
    path = ((getattr(request, "path_info", "") or request.path or "").strip()).lower()
    if path.startswith("/us/"):
        return "US"
    if path.startswith("/cl/"):
        return "CL"
    if path.startswith("/mx/"):
        return "MX"
    if path.startswith("/pe/"):
        return "PE"
    if path.startswith("/co/"):
        return "CO"
    if path.startswith("/ec/"):
        return "EC"
    if path.startswith("/ve/"):
        return "VE"
    if path.startswith("/br/"):
        return "BR"
    return str(fallback or "").upper() or None


class ClienteListView(CountryLangTemplateMixin, LoginRequiredMixin, TenantViewMixin, ListView):
    model = Cliente
    paginate_by = 50
    ordering = ("apellido", "nombre", "id")
    select_related_fields = (
        "color",
        "empresa",
        "region",
        "ciudad",
        "estado_usa",
        "ciudad_usa",
    )
    base_template_name = "clientes/cliente_list.html"  # Usar base_template_name para que CountryLangTemplateMixin funcione
    context_object_name = "cliente_list"

    def get_queryset(self):
        qs = super().get_queryset()
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                models.Q(nombre__icontains=q)
                | models.Q(apellido__icontains=q)
                | models.Q(email__icontains=q)
                | models.Q(telefono__icontains=q)
                | models.Q(tax_id__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = get_user_empresa_safe(self.request.user)

        if not empresa:
            return context

        # Obtener queryset base para estadísticas
        base_qs = Cliente.objects.filter(empresa=empresa)

        # Aplicar los mismos filtros de búsqueda a las estadísticas
        q = (self.request.GET.get("q") or "").strip()
        if q:
            base_qs = base_qs.filter(
                models.Q(nombre__icontains=q)
                | models.Q(apellido__icontains=q)
                | models.Q(email__icontains=q)
                | models.Q(telefono__icontains=q)
                | models.Q(tax_id__icontains=q)
            )

        hoy = date.today()
        hace_30_dias = hoy - timedelta(days=30)
        hace_7_dias = hoy - timedelta(days=7)
        inicio_mes = hoy.replace(day=1)

        # Calcular estadísticas
        estadisticas = base_qs.aggregate(
            total=Count("id"),
            con_vehiculos=Count("id", filter=Q(vehiculo__isnull=False), distinct=True),
            con_email=Count("id", filter=~Q(email__isnull=True) & ~Q(email="")),
            con_telefono=Count("id", filter=~Q(telefono__isnull=True) & ~Q(telefono="")),
            nuevos_mes=Count("id", filter=Q(created_at__date__gte=inicio_mes)),
            nuevos_30_dias=Count("id", filter=Q(created_at__date__gte=hace_30_dias)),
            nuevos_7_dias=Count("id", filter=Q(created_at__date__gte=hace_7_dias)),
        )

        # Clientes por ciudad (top 5)
        clientes_por_ciudad = (
            base_qs.values("ciudad__nombre")
            .annotate(cantidad=Count("id"))
            .order_by("-cantidad")[:5]
        )

        # Clientes con más vehículos (top 5)
        clientes_con_vehiculos = (
            base_qs.annotate(num_vehiculos=Count("vehiculo"))
            .filter(num_vehiculos__gt=0)
            .order_by("-num_vehiculos")[:5]
        )

        # Clientes activos (con documentos en los últimos 90 días)
        hace_90_dias = hoy - timedelta(days=90)
        try:
            from taller.models.documentos import Documento

            clientes_activos = (
                base_qs.filter(
                    documentos__fecha_emision__gte=hace_90_dias,
                    documentos__empresa=empresa,
                )
                .distinct()
                .count()
            )
        except Exception:
            clientes_activos = 0

        # Datos para gráfico de clientes nuevos por mes (últimos 6 meses)
        # Usar siempre día 1 para evitar ValueError (ej. 31 de nov no existe)
        from datetime import datetime

        datos_grafico = []
        mes_cursor = hoy.replace(day=1)

        for i in range(6):
            inicio_mes = mes_cursor

            if inicio_mes.month == 12:
                siguiente_mes = inicio_mes.replace(year=inicio_mes.year + 1, month=1, day=1)
            else:
                siguiente_mes = inicio_mes.replace(month=inicio_mes.month + 1, day=1)

            inicio_mes_dt = datetime.combine(inicio_mes, datetime.min.time())
            fin_mes_dt = datetime.combine(siguiente_mes, datetime.min.time())

            clientes_mes = base_qs.filter(
                created_at__gte=inicio_mes_dt,
                created_at__lt=fin_mes_dt,
            ).count()

            datos_grafico.append(
                {
                    "mes": inicio_mes.strftime("%b %Y"),
                    "cantidad": clientes_mes,
                }
            )

            if mes_cursor.month == 1:
                mes_cursor = mes_cursor.replace(year=mes_cursor.year - 1, month=12, day=1)
            else:
                mes_cursor = mes_cursor.replace(month=mes_cursor.month - 1, day=1)

        datos_grafico.reverse()  # Ordenar cronológicamente (más antiguo primero)

        context.update(
            {
                "estadisticas": estadisticas,
                "clientes_por_ciudad": list(clientes_por_ciudad),
                "clientes_con_vehiculos": list(clientes_con_vehiculos),
                "clientes_activos": clientes_activos,
                "datos_grafico": datos_grafico,
                "empresa": empresa,
            }
        )

        return context


class ClienteDetailView(CountryLangTemplateMixin, LoginRequiredMixin, TenantViewMixin, DetailView):
    model = Cliente
    base_template_name = "clientes/ver_cliente.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("empresa", "estado_usa", "ciudad_usa", "region", "ciudad", "color")
        )

    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)


class ClienteCreateView(
    CountryLangTemplateMixin,
    ContextReturnCreateMixin,
    LoginRequiredMixin,
    TenantViewMixin,
    CreateView,
):
    def get_default_success_url(self):
        from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

        # Flujo "crear cliente desde documento": usar ?next= para volver al formulario
        next_url = (self.request.POST.get("next") or self.request.GET.get("next") or "").strip()
        if next_url:
            from taller.mixins import safe_next_url

            safe = safe_next_url(next_url)
            if safe:
                # Añadir cliente_id para preselección en document form
                parsed = urlparse(safe)
                params = dict(parse_qsl(parsed.query, keep_blank_values=True))
                if self.object and getattr(self.object, "pk", None):
                    params["cliente_id"] = str(self.object.pk)
                new_query = urlencode(params)
                return urlunparse(parsed._replace(query=new_query))

        # Obtener el país de la empresa del usuario (usa/chile montan clientes sin "taller")
        return reverse_country_url(self.request, "clientes:lista_clientes")

    def get_created_object_payload(self):
        cliente = getattr(self, "object", None)
        if not cliente:
            return {}

        label = str(cliente)
        tax_id = getattr(cliente, "tax_id", "") or ""
        if tax_id and tax_id not in label:
            label = f"{label} · {tax_id}"

        return {
            "cliente_id": cliente.pk,
            "created_cliente_id": cliente.pk,
            "created_cliente_label": label,
        }

    CONSTRAINT_FIELD_MESSAGES = {
        "uq_cliente_empresa_email_present": (
            "email",
            "empresa_id, taller_cliente.email",
            "Ya existe un cliente con este email para esta empresa.",
        ),
        "uq_cliente_empresa_telefono_present": (
            "telefono",
            "empresa_id, taller_cliente.telefono",
            "Ya existe un cliente con este teléfono para esta empresa.",
        ),
        "uq_cliente_empresa_taxid_present": (
            "tax_id",
            "empresa_id, taller_cliente.tax_id",
            "Ya existe un cliente con este identificador tributario para esta empresa.",
        ),
    }

    def form_valid(self, form):
        from django.db import IntegrityError

        try:
            return super().form_valid(form)
        except IntegrityError as e:
            # PostgreSQL (psycopg2/psycopg3): el nombre del constraint viene en
            # e.__cause__.diag.constraint_name. SQLite no lo expone y en su
            # lugar lista los nombres de columna en el mensaje de texto — de
            # ahí el fallback por substring de columnas.
            constraint_name = getattr(getattr(e.__cause__, "diag", None), "constraint_name", None)
            message = str(e)

            for name, (field, column_hint, error_message) in self.CONSTRAINT_FIELD_MESSAGES.items():
                if constraint_name == name or name in message or column_hint in message:
                    if field in form.fields:
                        form.add_error(field, error_message)
                    else:
                        form.add_error(None, error_message)
                    return self.form_invalid(form)

            raise

    model = Cliente
    form_class = None  # Se setea en get_form_class
    base_template_name = "clientes/crear_cliente.html"  # Usar template existente

    def get_form_class(self):
        from taller.clientes.forms import ClienteForm

        return ClienteForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        empresa = get_user_empresa_safe(self.request.user)
        if empresa:
            kwargs["empresa"] = empresa
        kwargs["pais"] = _route_country(self.request, getattr(empresa, "pais", None))
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = get_user_empresa_safe(self.request.user)
        context["empresa"] = empresa
        context["empresa_actual"] = empresa

        # Pasar next para el hidden del form (flujo desde documento/form)
        context["next"] = self.request.GET.get("next") or self.request.POST.get("next") or ""
        context["return_to"] = (
            self.get_return_to()
            or self.request.GET.get("return_to")
            or self.request.POST.get("return_to")
            or ""
        )

        # Asegurar que el país esté disponible para el template
        pais = getattr(context.get("form"), "pais", None) or _route_country(
            self.request, getattr(empresa, "pais", None)
        )
        context["pais_usuario"] = pais
        context["usa_estado_ciudad"] = pais in STATE_CITY_COUNTRIES

        # Agregar colores disponibles al contexto
        from taller.models.color_cliente import ColorCliente

        if pais:
            context["colores_disponibles"] = ColorCliente.get_colores_para_pais(pais)
        else:
            context["colores_disponibles"] = ColorCliente.objects.filter(activo=True)

        # También asegurar que el formulario tenga la información del país
        if "form" in context:
            context["form"].pais = pais or getattr(context["form"], "pais", "CL")

        return context

    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)


class ClienteUpdateView(CountryLangTemplateMixin, LoginRequiredMixin, TenantViewMixin, UpdateView):
    model = Cliente
    form_class = None  # Se setea en get_form_class
    base_template_name = "clientes/cliente_form.html"

    def get_form_class(self):
        from taller.clientes.forms import ClienteForm

        return ClienteForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        empresa = get_user_empresa_safe(self.request.user)
        if empresa:
            kwargs["empresa"] = empresa
        kwargs["pais"] = _route_country(self.request, getattr(empresa, "pais", None))
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = get_user_empresa_safe(self.request.user)
        context["empresa"] = empresa
        context["empresa_actual"] = empresa

        # Asegurar que el país esté disponible para el template
        pais = getattr(context.get("form"), "pais", None) or _route_country(
            self.request, getattr(empresa, "pais", None)
        )
        context["pais_usuario"] = pais
        context["usa_estado_ciudad"] = pais in STATE_CITY_COUNTRIES

        # Agregar colores disponibles al contexto
        from taller.models.color_cliente import ColorCliente

        if pais:
            context["colores_disponibles"] = ColorCliente.get_colores_para_pais(pais)
        else:
            context["colores_disponibles"] = ColorCliente.objects.filter(activo=True)

        if "form" in context:
            context["form"].pais = pais or getattr(context["form"], "pais", "CL")

        return context

    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)

    def get_success_url(self):
        return reverse_country_url(self.request, "clientes:lista_clientes")
