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
    form_class = DocumentoForm  # el unificado
    template_name = "taller/documentos/editar_documento_nuevo.html"  # usar el moderno
    
    def dispatch(self, request, *a, **kw):
        obj = self.get_object()
        if obj.estado != "DRAFT":
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Documento no editable (no DRAFT).")
        return super().dispatch(request, *a, **kw)
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        doc = self.object

        # Repuestos
        repuestos = []
        for lr in doc.lineas_repuesto.all().select_related():
            repuestos.append({
                "codigo": lr.repuesto.part_number if getattr(lr, "repuesto", None) else "",
                "nombre": lr.nombre,
                "cantidad": lr.cantidad,
                "precio": float(lr.precio_unitario),
                "total": float(lr.cantidad * lr.precio_unitario),
            })

        # Servicios internos
        servicios = []
        for ls in doc.lineas_servicio.all().select_related():
            servicios.append({
                "nombre": ls.nombre,
                "precio": float(ls.precio_unitario),
            })

        # Otros servicios (externos)
        otros = []
        for lo in doc.lineas_otro_servicio.all():
            otros.append({
                "nombre_servicio": lo.nombre,
                "empresa_externa": lo.empresa_externa or "",
                "costo_interno": float(lo.costo_interno or 0),
                "precio_cliente": float(lo.precio_cliente or 0),
                "ganancia": float((lo.precio_cliente or 0) - (lo.costo_interno or 0)),
                "observaciones": getattr(lo, "observaciones", "") or "",
            })

        subtotal_repuestos = sum(i["total"] for i in repuestos)
        subtotal_servicios = sum(i["precio"] for i in servicios)
        subtotal_otros = sum(i["precio_cliente"] for i in otros)
        subtotal = subtotal_repuestos + subtotal_servicios + subtotal_otros

        # Si el form tiene incluir_iva, úsalo, si no, default False
        incluir_iva = getattr(doc, "incluir_iva", False)
        iva = round(subtotal * 0.19) if incluir_iva else 0
        total = subtotal + iva

        ctx.update({
            "repuestos": repuestos,
            "servicios": servicios,
            "otros_servicios": otros,
            "subtotal_repuestos": subtotal_repuestos,
            "subtotal_servicios": subtotal_servicios,
            "subtotal": subtotal,
            "iva": iva,
            "total": total,
        })
        return ctx
