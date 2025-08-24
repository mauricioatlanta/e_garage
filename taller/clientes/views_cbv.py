from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from core.views import TenantViewMixin
from taller.models.clientes import Cliente

class ClienteListView(LoginRequiredMixin, TenantViewMixin, ListView):
    model = Cliente
    paginate_by = 50
    ordering = ("apellido", "nombre", "id")
    select_related_fields = ()

    def get_queryset(self):
        qs = super().get_queryset()
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                models.Q(nombre__icontains=q) |
                models.Q(apellido__icontains=q) |
                models.Q(email__icontains=q) |
                models.Q(telefono__icontains=q) |
                models.Q(tax_id__icontains=q)
            )
        return qs

class ClienteDetailView(LoginRequiredMixin, TenantViewMixin, DetailView):
    model = Cliente
    
    def get_queryset(self):
        return super().get_queryset().select_related('empresa', 'estado_usa', 'ciudad_usa', 'region', 'ciudad')

class ClienteCreateView(LoginRequiredMixin, TenantViewMixin, CreateView):
    def get_success_url(self):
        from django.urls import reverse
        return reverse('clientes:lista_clientes')
    def form_valid(self, form):
        from django.db import IntegrityError
        try:
            return super().form_valid(form)
        except IntegrityError as e:
            if 'taller_cliente.empresa_id, taller_cliente.email' in str(e):
                form.add_error('email', 'Ya existe un cliente con este email para esta empresa.')
                return self.form_invalid(form)
            raise

    model = Cliente
    form_class = None  # Se setea en get_form_class

    def get_form_class(self):
        from taller.clientes.forms import ClienteForm
        return ClienteForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        empresa = getattr(self.request.user, 'empresa', None)
        if empresa:
            kwargs['empresa'] = empresa
        return kwargs

    def get_template_names(self):
        empresa = getattr(self.request.user, 'empresa', None)
        if empresa and getattr(empresa, 'pais', None) == 'US':
            return ['taller/clientes/crear_cliente.html']  # Template específico para USA si existe
        return ['taller/cliente_form.html']  # Template por defecto (Chile o global)

class ClienteUpdateView(LoginRequiredMixin, TenantViewMixin, UpdateView):
    model = Cliente
    form_class = None  # Se setea en get_form_class
    template_name = "taller/clientes/editar_cliente.html"

    def get_form_class(self):
        from taller.clientes.forms import ClienteForm
        return ClienteForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        empresa = getattr(self.request.user, 'empresa', None)
        if empresa:
            kwargs['empresa'] = empresa
        return kwargs

    def get_success_url(self):
        from django.urls import reverse
        return reverse('taller:clientes:lista_clientes')
