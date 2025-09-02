from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from core.views import TenantViewMixin
from taller.servicios.models import Servicio, CategoriaServicio, SubcategoriaServicio

class ServicioListView(LoginRequiredMixin, TenantViewMixin, ListView):
    model = Servicio
    template_name = "servicios/servicios_menu.html"
    select_related_fields = ("categoria","subcategoria")
    paginate_by = 50
    ordering = ("nombre", "id")
    
    def get_queryset(self):
        qs = super().get_queryset()
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                models.Q(nombre__icontains=q) |
                models.Q(categoria__nombre__icontains=q) |
                models.Q(subcategoria__nombre__icontains=q)
            )
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = CategoriaServicio.objects.all()
        context['subcategorias'] = SubcategoriaServicio.objects.all()
        return context

class ServicioDetailView(LoginRequiredMixin, TenantViewMixin, DetailView):
    model = Servicio
    template_name = "servicios/servicio_detail.html"
    select_related_fields = ("categoria","subcategoria")

class ServicioCreateView(LoginRequiredMixin, TenantViewMixin, CreateView):
    model = Servicio
    template_name = "servicios/crear_servicio.html"
    fields = ["nombre", "categoria", "subcategoria"]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = CategoriaServicio.objects.all()
        context['subcategorias'] = SubcategoriaServicio.objects.all()
        return context

class ServicioUpdateView(LoginRequiredMixin, TenantViewMixin, UpdateView):
    model = Servicio
    template_name = "servicios/editar_servicio.html"
    fields = ["nombre", "categoria", "subcategoria"]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = CategoriaServicio.objects.all()
        context['subcategorias'] = SubcategoriaServicio.objects.all()
        return context
