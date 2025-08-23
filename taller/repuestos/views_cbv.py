from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from core.views import TenantViewMixin
from taller.models.repuesto import Repuesto

class RepuestoListView(LoginRequiredMixin, TenantViewMixin, ListView):
    model = Repuesto
    select_related_fields = ("categoria",)
    paginate_by = 50
    ordering = ("nombre", "id")
    def get_queryset(self):
        qs = super().get_queryset()
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                models.Q(part_number__icontains=q) |
                models.Q(nombre__icontains=q) |
                models.Q(categoria__nombre__icontains=q)
            )
        return qs

class RepuestoDetailView(LoginRequiredMixin, TenantViewMixin, DetailView):
    model = Repuesto
    select_related_fields = ("categoria",)

class RepuestoCreateView(LoginRequiredMixin, TenantViewMixin, CreateView):
    model = Repuesto
    fields = ["part_number", "nombre", "categoria", "precio_compra", "precio_venta", "cantidad_stock", "proveedor"]
    template_name = 'taller/repuesto_form.html'
    success_url = reverse_lazy('taller:repuestos:lista_repuestos')

class RepuestoUpdateView(LoginRequiredMixin, TenantViewMixin, UpdateView):
    model = Repuesto
    fields = ["part_number", "nombre", "categoria", "precio_compra", "precio_venta", "cantidad_stock", "proveedor"]
    template_name = 'taller/repuesto_form.html'
    success_url = reverse_lazy('taller:repuestos:lista_repuestos')
