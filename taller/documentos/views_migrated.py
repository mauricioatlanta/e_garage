"""
Vistas de documentos migradas para usar CountryLangTemplateMixin
Esto reemplaza las vistas FBV que están en views.py con plantillas hardcodeadas
"""

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.http import JsonResponse
from django.contrib import messages
from django.utils.translation import get_language
from decimal import Decimal

from taller.mixins import CountryLangTemplateMixin
from taller.models import Documento, Tecnico
from taller.forms.documento import DocumentoForm


@method_decorator(login_required, name='dispatch')
class DocumentoListView(CountryLangTemplateMixin, ListView):
    """Vista para listar documentos de la empresa"""
    model = Documento
    context_object_name = 'documentos'
    base_template_name = "documentos/lista_documentos.html"
    paginate_by = 20
    
    def get_queryset(self):
        """Filtrar documentos por empresa del usuario"""
        try:
            empresa = self.request.user.empresa
            return Documento.objects.filter(empresa=empresa).select_related(
                'cliente', 'vehiculo', 'tecnico_responsable'
            ).order_by('-fecha_emision', '-id')
        except AttributeError:
            return Documento.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['country'] = getattr(self.request.user.empresa, 'pais', 'cl').lower()
        return context
    
    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)


@method_decorator(login_required, name='dispatch')
class DocumentoCreateView(CountryLangTemplateMixin, CreateView):
    """Vista para crear documentos"""
    model = Documento
    form_class = DocumentoForm
    base_template_name = "documentos/crear_documento.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = self.request.user.empresa
        
        # Cargar mecánicos activos del taller
        mecanicos = Tecnico.objects.filter(empresa=empresa, activo=True)
        
        context.update({
            'mecanicos': mecanicos,
            'es_edicion': False,
            'company_country': getattr(self.request, 'company_country', None),
        })
        return context
    
    def form_valid(self, form):
        form.instance.empresa = self.request.user.empresa
        return super().form_valid(form)
    
    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)


@method_decorator(login_required, name='dispatch')
class DocumentoDetailView(CountryLangTemplateMixin, DetailView):
    """Vista para ver detalles de un documento"""
    model = Documento
    context_object_name = 'documento'
    base_template_name = "documentos/ver_documento_nuevo.html"
    
    def get_queryset(self):
        """Asegurar que solo se vean documentos de la empresa"""
        return Documento.objects.filter(empresa=self.request.user.empresa)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documento = self.object
        
        # Obtener líneas del documento
        repuestos = documento.lineas.filter(tipo='repuesto').select_related('repuesto')
        servicios = documento.lineas.filter(tipo='servicio').select_related('servicio_interno')
        otros_servicios = documento.lineas.filter(tipo='otro_servicio')
        
        # Calcular subtotales
        subtotal_repuestos = sum(
            linea.precio_unitario * linea.cantidad 
            for linea in repuestos
        )
        subtotal_servicios = sum(
            linea.precio_unitario * linea.cantidad 
            for linea in servicios
        )
        subtotal_otros_servicios = sum(
            getattr(otro, 'precio_cliente', Decimal('0.00')) 
            for otro in otros_servicios
        )
        
        subtotal = subtotal_repuestos + subtotal_servicios + subtotal_otros_servicios
        
        # Calcular IVA (19% solo sobre repuestos según la lógica de negocio)
        iva = subtotal_repuestos * Decimal('0.19')
        total = subtotal + iva
        
        context.update({
            'lineas_repuesto': repuestos,
            'lineas_servicio': servicios, 
            'lineas_otro_servicio': otros_servicios,
            'repuestos': repuestos,  # Mantener compatibilidad
            'servicios': servicios,   # Mantener compatibilidad
            'subtotal_repuestos': subtotal_repuestos,
            'subtotal_servicios': subtotal_servicios,
            'subtotal_otros_servicios': subtotal_otros_servicios,
            'subtotal': subtotal,
            'iva': iva,
            'total': total,
        })
        return context
    
    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)


@method_decorator(login_required, name='dispatch')
class DocumentoUpdateView(CountryLangTemplateMixin, UpdateView):
    """Vista para editar documentos"""
    model = Documento
    form_class = DocumentoForm
    base_template_name = "documentos/editar_documento_nuevo.html"
    
    def get_queryset(self):
        """Asegurar que solo se editen documentos de la empresa"""
        return Documento.objects.filter(empresa=self.request.user.empresa)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documento = self.object
        empresa = self.request.user.empresa
        
        # Obtener líneas del documento para edición
        servicios = documento.lineas.filter(tipo='servicio').select_related('servicio_interno')
        repuestos = documento.lineas.filter(tipo='repuesto').select_related('repuesto')
        otros_servicios = documento.lineas.filter(tipo='otro_servicio')
        
        # Calcular subtotales
        subtotal_repuestos = sum(
            linea.precio_unitario * linea.cantidad 
            for linea in repuestos
        )
        
        # Cargar mecánicos activos del taller
        mecanicos = Tecnico.objects.filter(empresa=empresa, activo=True)
        
        context.update({
            'documento': documento,
            'servicios': servicios,
            'repuestos': repuestos,
            'otros_servicios': otros_servicios,
            'subtotal_repuestos': subtotal_repuestos,
            'mecanicos': mecanicos,
            'es_edicion': True,
        })
        return context
    
    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)


@method_decorator(login_required, name='dispatch')
class DocumentoDeleteView(CountryLangTemplateMixin, DeleteView):
    """Vista para eliminar documentos"""
    model = Documento
    base_template_name = "documentos/confirmar_eliminar.html"
    success_url = "/documentos/"
    
    def get_queryset(self):
        """Asegurar que solo se eliminen documentos de la empresa"""
        return Documento.objects.filter(empresa=self.request.user.empresa)
    
    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)
