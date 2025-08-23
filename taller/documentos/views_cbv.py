from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from core.views import TenantViewMixin
from .models import Documento
from .forms import DocumentoForm

class DocumentoListView(LoginRequiredMixin, TenantViewMixin, ListView):
    model = Documento
    select_related_fields = ("cliente","vehiculo")
    prefetch_related_fields = ("lineas",)
    paginate_by = 50
    ordering = ("-fecha_emision","-id")
    def get_queryset(self):
        qs = super().get_queryset()
        q = (self.request.GET.get("q") or "").strip()
        if q:
            qs = qs.filter(
                models.Q(numero__icontains=q) |
                models.Q(cliente__nombre__icontains=q) |
                models.Q(cliente__apellido__icontains=q) |
                models.Q(vehiculo__patente__icontains=q) |
                models.Q(vehiculo__vin__icontains=q)
            )
        estado = self.request.GET.get("estado")
        if estado:
            qs = qs.filter(estado=estado)
        return qs

class DocumentoDetailView(LoginRequiredMixin, TenantViewMixin, DetailView):
    model = Documento
    select_related_fields = ("cliente", "vehiculo", "tecnico_responsable")
    prefetch_related_fields = ("lineas_repuesto", "lineas_servicio", "lineas_otro_servicio")

class DocumentoCreateView(LoginRequiredMixin, TenantViewMixin, CreateView):
    model = Documento
    form_class = DocumentoForm

class DocumentoUpdateView(LoginRequiredMixin, TenantViewMixin, UpdateView):
    model = Documento
    form_class = DocumentoForm
    def dispatch(self, request, *a, **kw):
        obj = self.get_object()
        if obj.estado != "DRAFT":
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Documento no editable (no DRAFT).")
        return super().dispatch(request, *a, **kw)
