from datetime import date, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.views import TenantViewMixin
from taller.common.mixins.return_to_document import ReturnToDocumentMixin
from taller.mixins import CountryLangTemplateMixin
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.utils.empresa import get_user_empresa_safe


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
    ReturnToDocumentMixin,
    CountryLangTemplateMixin,
    LoginRequiredMixin,
    TenantViewMixin,
    CreateView,
):
    entity_type = "cliente"

    def _is_ajax_request(self):
        return (
            self.request.headers.get("x-requested-with") == "XMLHttpRequest"
            or self.request.GET.get("ajax") == "1"
            or self.request.POST.get("ajax") == "1"
        )

    def _is_modal_request(self):
        return (
            self.request.GET.get("modal") or self.request.POST.get("modal") or ""
        ).strip() == "1"

    def _build_cliente_payload(self):
        nombre = " ".join(
            part.strip()
            for part in [
                getattr(self.object, "nombre", "") or "",
                getattr(self.object, "apellido", "") or "",
            ]
            if part and part.strip()
        ).strip()
        if not nombre:
            nombre = f"Cliente #{self.object.pk}"
        return {
            "id": self.object.pk,
            "nombre": nombre,
            "email": getattr(self.object, "email", "") or "",
            "telefono": getattr(self.object, "telefono", "") or "",
        }

    def get_success_url(self):
        from django.urls import reverse

        has_return = bool(
            (
                self.request.POST.get(self.return_param_name)
                or self.request.GET.get(self.return_param_name)
            )
            or (
                self.request.POST.get(self.legacy_return_param_name)
                or self.request.GET.get(self.legacy_return_param_name)
            )
        )
        if has_return:
            return ReturnToDocumentMixin.get_success_url(self)

        # Obtener el país de la empresa del usuario (usa/chile montan clientes sin "taller")
        empresa = get_user_empresa_safe(self.request.user)
        if empresa and empresa.pais == "US":
            return reverse("usa:clientes:lista_clientes")
        return reverse("chile:clientes:lista_clientes")

    def get_created_label(self, obj):
        nombre = " ".join(
            part.strip()
            for part in [getattr(obj, "nombre", "") or "", getattr(obj, "apellido", "") or ""]
            if part and part.strip()
        ).strip()
        return nombre or super().get_created_label(obj)

    def get_context_redirect_params(self, obj):
        params = super().get_context_redirect_params(obj)
        params.setdefault("cliente_id", str(getattr(obj, "pk", "") or ""))
        params.setdefault("cliente_nombre", self.get_created_label(obj))
        return params

    def form_valid(self, form):
        from django.db import IntegrityError

        try:
            response = super().form_valid(form)
        except IntegrityError as e:
            if "taller_cliente.empresa_id, taller_cliente.email" in str(e):
                form.add_error("email", "Ya existe un cliente con este email para esta empresa.")
                return self.form_invalid(form)
            raise

        if self._is_ajax_request():
            return JsonResponse(
                {"success": True, "cliente": self._build_cliente_payload()},
                status=201,
            )

        if self._is_modal_request():
            cliente = self._build_cliente_payload()
            next_url = self.get_success_url()
            html = f"""<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><title>Cliente creado</title></head>
<body>
<script>
(function() {{
  var payload = {{
    type: 'eg:cliente-created',
    cliente: {{
      id: '{cliente["id"]}',
      nombre: {cliente["nombre"]!r},
      email: {cliente["email"]!r},
      telefono: {cliente["telefono"]!r}
    }},
    next: {next_url!r}
  }};
  if (window.parent && window.parent !== window) {{
    window.parent.postMessage(payload, window.location.origin);
  }}
}})();
</script>
<p>Cliente creado. Puedes cerrar esta ventana.</p>
</body>
</html>"""
            return HttpResponse(html)

        return response

    def form_invalid(self, form):
        if self._is_ajax_request():
            return JsonResponse(
                {"success": False, "errors": form.errors.get_json_data()},
                status=400,
            )
        return super().form_invalid(form)

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
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = get_user_empresa_safe(self.request.user)
        context["empresa"] = empresa
        context["empresa_actual"] = empresa

        # Pasar next para el hidden del form (flujo desde documento/form)
        context["next"] = self.request.GET.get("next") or self.request.POST.get("next") or ""
        context["return_to"] = (
            self.request.GET.get(self.return_param_name)
            or self.request.POST.get(self.return_param_name)
            or context["next"]
            or ""
        )
        context["field_target"] = (
            self.request.GET.get(self.field_target_param)
            or self.request.POST.get(self.field_target_param)
            or "cliente"
        )
        context["modal_mode"] = self._is_modal_request()
        context["ajax_mode"] = self._is_ajax_request()

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
        empresa = get_user_empresa_safe(self.request.user)
        if empresa:
            kwargs["empresa"] = empresa
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = get_user_empresa_safe(self.request.user)
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

        return reverse("chile:taller:clientes:lista_clientes")
