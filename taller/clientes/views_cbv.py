from datetime import date, timedelta

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
        from datetime import datetime

        datos_grafico = []
        for i in range(6):
            mes_fecha = hoy.replace(day=1) - timedelta(days=30 * i)
            if mes_fecha.month == 1:
                mes_anterior = mes_fecha.replace(year=mes_fecha.year - 1, month=12)
            else:
                mes_anterior = mes_fecha.replace(month=mes_fecha.month - 1)

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
    def get_success_url(self):
        from django.urls import reverse

        # Obtener el país de la empresa del usuario
        empresa = getattr(self.request.user, "empresa", None)
        if empresa and empresa.pais == "US":
            # Usuario de USA: redirigir a namespace de USA
            return reverse("usa:taller:clientes:lista_clientes")
        else:
            # Usuario de Chile o fallback: redirigir a namespace de Chile
            return reverse("chile:taller:clientes:lista_clientes")

    def form_valid(self, form):
        from django.db import IntegrityError

        try:
            return super().form_valid(form)
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

        return reverse("chile:taller:clientes:lista_clientes")
