from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from core.views import TenantViewMixin
from taller.servicios.models import Servicio

class ServicioListView(LoginRequiredMixin, TenantViewMixin, ListView):
    model = Servicio
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

class ServicioDetailView(LoginRequiredMixin, TenantViewMixin, DetailView):
    model = Servicio
    select_related_fields = ("categoria","subcategoria")

class ServicioCreateView(LoginRequiredMixin, TenantViewMixin, CreateView):
    model = Servicio
    fields = ["nombre", "categoria", "subcategoria"]

class ServicioUpdateView(LoginRequiredMixin, TenantViewMixin, UpdateView):
    model = Servicio
    fields = ["nombre", "categoria", "subcategoria"]
