from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Count, Q
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.views import TenantViewMixin
from taller.mixins import CountryLangTemplateMixin
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo


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
        empresa = getattr(self.request.user, "empresa", None)

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
            from taller.models.documento import Documento

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
        from datetime import datetime

        datos_grafico = []
        for i in range(6):
            mes_fecha = hoy.replace(day=1) - timedelta(days=30 * i)
            mes_anterior = mes_fecha - relativedelta(months=1)

            # Convertir a datetime para comparar con created_at
            inicio_mes_dt = datetime.combine(mes_anterior, datetime.min.time())
            fin_mes_dt = datetime.combine(mes_fecha + timedelta(days=32), datetime.min.time())

            clientes_mes = base_qs.filter(
                created_at__gte=inicio_mes_dt, created_at__lt=fin_mes_dt
            ).count()

            datos_grafico.append(
                {
                    "mes": mes_fecha.strftime("%b %Y"),
                    "cantidad": clientes_mes,
                }
            )

        datos_grafico.reverse()  # Ordenar cronológicamente

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


class ClienteCreateView(CountryLangTemplateMixin, LoginRequiredMixin, TenantViewMixin, CreateView):
    SESSION_NEXT_KEY = "clientes_create_next"

    def dispatch(self, request, *args, **kwargs):
        # Asegurar que la empresa existe y dejarla en request para no tocar user.empresa (evita 500 si falta columna is_trial)
        try:
            from taller.utils.empresa import get_or_create_empresa

            request.empresa = get_or_create_empresa(request)
        except Exception as e:
            # PermissionDenied → dejar que suba; OperationalError u otro → evitar 500
            from django.core.exceptions import PermissionDenied
            from django.db.utils import OperationalError

            if isinstance(e, PermissionDenied):
                raise
            request.empresa = None
        # Si viene next en GET, guardarlo en sesión (fallback robusto si el hidden falta o se pierde)
        next_url = (request.GET.get("next") or "").strip()
        if next_url:
            request.session[self.SESSION_NEXT_KEY] = next_url
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        from urllib.parse import unquote

        from django.urls import reverse
        from django.utils.http import url_has_allowed_host_and_scheme

        # 1) POST, 2) GET, 3) SESSION (fallback robusto si el template no envió el hidden)
        raw_next = (
            self.request.POST.get("next")
            or self.request.GET.get("next")
            or self.request.session.pop(self.SESSION_NEXT_KEY, "")
        ).strip()
        if raw_next:
            # Por si quedó doble-encoded o similar
            next_url = unquote(raw_next).strip()

            # Normalizar "us/..." -> "/us/..."
            if next_url and not next_url.startswith(("http://", "https://", "/")):
                next_url = "/" + next_url

            # Validar: permitir relativo seguro o absoluto del mismo host
            url_to_check = (
                self.request.build_absolute_uri(next_url) if next_url.startswith("/") else next_url
            )
            if url_has_allowed_host_and_scheme(
                url=url_to_check,
                allowed_hosts={self.request.get_host()},
                require_https=self.request.is_secure(),
            ):
                # Devolver ruta relativa para redirect (sin origin)
                if next_url.startswith("/"):
                    return next_url
                # Si era absoluta del mismo host, devolver path
                from urllib.parse import urlparse

                return urlparse(next_url).path or next_url

        # Fallback: lista de clientes según prefijo de la URL (namespaces correctos sin "taller")
        path = (getattr(self.request, "path_info", "") or self.request.path or "").lower()
        if "/us/en/" in path or path == "/us/en":
            return reverse("us_en:clientes:lista_clientes")
        if "/us/es/" in path or path == "/us/es":
            return reverse("us_es:clientes:lista_clientes")
        if "/us/" in path:
            return reverse("usa:clientes:lista_clientes")
        return reverse("chile:clientes:lista_clientes")

    def form_valid(self, form):
        from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

        from django.db import IntegrityError
        from django.shortcuts import redirect

        try:
            self.object = form.save()
            next_url = self.get_success_url()
            # Si volvemos al documento, agregar prefill_cliente para autoseleccionar
            if next_url and "documentos" in next_url:
                parsed = urlparse(next_url)
                params = parse_qs(parsed.query, keep_blank_values=True)
                params["prefill_cliente"] = [str(self.object.pk)]

                # ✅ Enviar datos completos para no depender de AJAX
                nombre = ""
                try:
                    nombre = (getattr(self.object, "nombre_completo", None) or "").strip()
                except Exception:
                    nombre = ""

                if not nombre:
                    nombre = f"{(getattr(self.object, 'nombre', '') or '').strip()} {(getattr(self.object, 'apellido', '') or '').strip()}".strip()

                params["prefill_cliente_nombre"] = [nombre or str(self.object)]
                params["prefill_cliente_email"] = [getattr(self.object, "email", "") or ""]
                params["prefill_cliente_telefono"] = [getattr(self.object, "telefono", "") or ""]

                new_query = urlencode(params, doseq=True)
                next_url = urlunparse(parsed._replace(query=new_query))
            return redirect(next_url)
        except IntegrityError as e:
            if "taller_cliente.empresa_id, taller_cliente.email" in str(e):
                form.add_error("email", "Ya existe un cliente con este email para esta empresa.")
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
        empresa = getattr(self.request, "empresa", None)
        if empresa:
            kwargs["empresa"] = empresa

        # País desde URL primero (ej. /us/en/clientes/crear/ → US), para que
        # el formulario muestre estado/ciudad aunque la empresa sea de otro país.
        try:
            from taller.config.country_settings import CountrySettings

            pais_from_url = CountrySettings.get_country_from_url(
                getattr(self.request, "path_info", "") or self.request.path or ""
            )
        except Exception:
            pais_from_url = None

        if pais_from_url:
            kwargs["pais"] = (
                pais_from_url.upper() if isinstance(pais_from_url, str) else pais_from_url
            )
        else:
            path = (getattr(self.request, "path_info", "") or self.request.path or "").lower()
            parts = [p for p in path.split("/") if p]
            prefix = parts[0] if parts else ""
            if prefix in {"us", "cl", "mx", "pe", "co", "ec", "ve", "br"}:
                kwargs["pais"] = prefix.upper()
            elif empresa and hasattr(empresa, "pais") and getattr(empresa, "pais", None):
                kwargs["pais"] = empresa.pais

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = getattr(self.request, "empresa", None)
        context["empresa"] = empresa
        context["empresa_actual"] = empresa
        # Pasar next para que el template lo incluya en el hidden y el POST redirija de vuelta (ej. al formulario de documento)
        context["next"] = self.request.GET.get("next", "").strip() or None

        # País para el template: priorizar URL (ej. /us/en/ → US) para coincidir con el template.
        try:
            from taller.config.country_settings import CountrySettings

            pais = CountrySettings.get_country_from_url(
                getattr(self.request, "path_info", "") or self.request.path or ""
            )
            if pais and isinstance(pais, str):
                pais = pais.upper()
        except Exception:
            pais = None

        if not pais:
            path = (getattr(self.request, "path_info", "") or self.request.path or "").lower()
            parts = [p for p in path.split("/") if p]
            prefix = parts[0] if parts else ""
            if prefix in {"us", "cl", "mx", "pe", "co", "ec", "ve", "br"}:
                pais = prefix.upper()
            elif empresa and hasattr(empresa, "pais"):
                try:
                    pais = empresa.pais
                except Exception:
                    pais = None
            else:
                pais = None
        context["pais_usuario"] = pais
        context["usa_estado_ciudad"] = pais in {"US", "BR", "VE", "PE", "MX"}

        # Agregar colores disponibles al contexto (defensivo por columnas faltantes en BD)
        try:
            from taller.models.color_cliente import ColorCliente

            if pais:
                context["colores_disponibles"] = ColorCliente.get_colores_para_pais(pais)
            else:
                context["colores_disponibles"] = ColorCliente.objects.filter(activo=True)
        except Exception:
            context["colores_disponibles"] = []

        # También asegurar que el formulario tenga la información del país
        if "form" in context:
            context["form"].pais = pais

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
        empresa = getattr(self.request.user, "empresa", None)
        if empresa:
            kwargs["empresa"] = empresa
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = getattr(self.request.user, "empresa", None)
        context["empresa"] = empresa
        context["empresa_actual"] = empresa

        # Asegurar que el país esté disponible para el template
        pais = None
        if empresa and hasattr(empresa, "pais"):
            pais = empresa.pais
        context["pais_usuario"] = pais
        context["usa_estado_ciudad"] = pais in {"US", "BR", "VE", "PE", "MX"}

        # Agregar colores disponibles al contexto
        from taller.models.color_cliente import ColorCliente

        if pais:
            context["colores_disponibles"] = ColorCliente.get_colores_para_pais(pais)
        else:
            context["colores_disponibles"] = ColorCliente.objects.filter(activo=True)

        return context

    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)

    def get_success_url(self):
        from django.urls import reverse

        path = (getattr(self.request, "path_info", "") or self.request.path or "").lower()
        if "/us/en/" in path or path == "/us/en":
            return reverse("us_en:clientes:lista_clientes")
        if "/us/es/" in path or path == "/us/es":
            return reverse("us_es:clientes:lista_clientes")
        if "/us/" in path:
            return reverse("usa:clientes:lista_clientes")
        return reverse("chile:clientes:lista_clientes")
