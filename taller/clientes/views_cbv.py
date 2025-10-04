from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.views import TenantViewMixin
from taller.mixins import CountryLangTemplateMixin
from taller.models.clientes import Cliente


class ClienteListView(
    CountryLangTemplateMixin, LoginRequiredMixin, TenantViewMixin, ListView
):
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
    template_name = "clientes/cliente_list.html"
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


class ClienteDetailView(
    CountryLangTemplateMixin, LoginRequiredMixin, TenantViewMixin, DetailView
):
    model = Cliente
    base_template_name = "clientes/ver_cliente.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related(
                "empresa", "estado_usa", "ciudad_usa", "region", "ciudad", "color"
            )
        )

    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)


class ClienteCreateView(
    CountryLangTemplateMixin, LoginRequiredMixin, TenantViewMixin, CreateView
):
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
                form.add_error(
                    "email", "Ya existe un cliente con este email para esta empresa."
                )
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


class ClienteUpdateView(
    CountryLangTemplateMixin, LoginRequiredMixin, TenantViewMixin, UpdateView
):
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
