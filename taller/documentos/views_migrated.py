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
from django.utils import translation
from django.template.loader import select_template
from django.template import TemplateDoesNotExist
from decimal import Decimal
from django.db.models import Sum, F, Value, DecimalField, Count, IntegerField
from django.db.models.functions import Coalesce

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
        """Filtrar documentos por empresa del usuario con anotaciones para el template"""
        try:
            empresa = self.request.user.empresa
            return (
                Documento.objects
                .filter(empresa=empresa)
                .select_related('cliente', 'vehiculo', 'tecnico_responsable')
                .annotate(
                    # Conteos de líneas
                    rep_count=Count('lineas_repuesto', distinct=True),
                    serv_count=Count('lineas_servicio', distinct=True),
                    otros_count=Count('lineas_otro_servicio', distinct=True),
                    
                    # Sumas monetarias
                    sum_rep=Coalesce(
                        Sum(
                            F('lineas_repuesto__cantidad') * F('lineas_repuesto__precio_unitario') * (1 - F('lineas_repuesto__descuento') / 100),
                            output_field=DecimalField(max_digits=12, decimal_places=2)
                        ),
                        Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
                    ),
                    sum_serv=Coalesce(
                        Sum(
                            F('lineas_servicio__cantidad') * F('lineas_servicio__precio_unitario') * (1 - F('lineas_servicio__descuento') / 100),
                            output_field=DecimalField(max_digits=12, decimal_places=2)
                        ),
                        Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
                    ),
                    sum_out=Coalesce(
                        Sum(
                            F('lineas_otro_servicio__precio_cliente') * F('lineas_otro_servicio__cantidad'),
                            output_field=DecimalField(max_digits=12, decimal_places=2)
                        ),
                        Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
                    ),
                )
                .annotate(
                    # Total general calculado
                    total_general_anotado=F('sum_rep') + F('sum_serv') + F('sum_out')
                )
                .order_by('-fecha_emision', '-id')
            )
        except AttributeError:
            return Documento.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['country'] = getattr(self.request.user.empresa, 'pais', 'cl').lower()
        
        # Calcular total de facturas (excluyendo órdenes de trabajo y presupuestos)
        from django.db.models import Sum, Count
        facturas_stats = self.get_queryset().filter(tipo='FAC').aggregate(
            total_facturas=Sum('total_general_anotado'),
            count_facturas=Count('id')
        )
        
        context.update({
            'total_facturas': facturas_stats['total_facturas'] or 0,
            'count_facturas': facturas_stats['count_facturas'] or 0
        })
        
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
        repuestos = documento.lineas_repuesto.all()
        servicios = documento.lineas_servicio.all()
        otros_servicios = documento.lineas_otro_servicio.all()
        
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
            'company_country': getattr(self.request, 'company_country', None),
        })
        return context
    
    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)


@method_decorator(login_required, name='dispatch')
class DocumentoUpdateView(UpdateView):
    """Vista para editar documentos"""
    model = Documento
    form_class = DocumentoForm
    
    def _resolve_template(self):
        user = self.request.user
        country = (getattr(getattr(user, 'empresa', None), 'country', 'CL') or 'CL').lower()
        lang = (translation.get_language() or 'es').lower()

        # Candidatos SIN el duplicado "taller/common/taller"
        candidates = [
            f"taller/{country}/{lang}/documentos/editar_documento_nuevo.html",
            f"taller/{country}/{lang}/documentos/documento_form.html",
            f"taller/{country}/es/documentos/documento_form.html",
            f"taller/{country}/es/documentos/editar_documento_nuevo.html",
            "taller/documentos/editar_documento_nuevo.html",
            "taller/documentos/documento_form.html",
        ]
        return select_template(candidates).template.name

    def get_template_names(self):
        try:
            return [self._resolve_template()]
        except TemplateDoesNotExist:
            # último fallback: evita 500 / página en blanco
            return ["taller/documentos/documento_form.html"]
    
    def get_queryset(self):
        """Asegurar que solo se editen documentos de la empresa"""
        return Documento.objects.filter(empresa=self.request.user.empresa)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        documento = self.object
        empresa = self.request.user.empresa
        
        # Obtener líneas del documento para edición
        servicios = documento.lineas_servicio.all()
        repuestos = documento.lineas_repuesto.all()
        otros_servicios = documento.lineas_otro_servicio.all()
        
        # Calcular subtotales directamente
        subtotal_repuestos = sum(
            linea.precio_unitario * linea.cantidad 
            for linea in repuestos
        )
        
        subtotal_servicios = sum(
            linea.precio_unitario * linea.cantidad 
            for linea in servicios
        )
        
        subtotal_otros_servicios = sum(
            otro.precio_cliente * otro.cantidad
            for otro in otros_servicios
        )
        
        subtotal = subtotal_repuestos + subtotal_servicios + subtotal_otros_servicios
        
        # Calcular IVA (19% solo sobre repuestos según la lógica de negocio)
        iva = subtotal_repuestos * Decimal('0.19')
        total = subtotal + iva
        
        # Cargar mecánicos activos del taller
        mecanicos = Tecnico.objects.filter(empresa=empresa, activo=True)
        
        context.update({
            'documento': documento,
            'servicios': servicios,
            'repuestos': repuestos,
            'otros_servicios': otros_servicios,
            'subtotal_repuestos': subtotal_repuestos,
            'subtotal_servicios': subtotal_servicios,
            'subtotal_otros_servicios': subtotal_otros_servicios,
            'subtotal': subtotal,
            'iva': iva,
            'total': total,
            'mecanicos': mecanicos,
            'es_edicion': True,
            'company_country': getattr(self.request, 'company_country', None),
            # Debug info
            'debug_servicios_count': servicios.count(),
            'debug_otros_count': otros_servicios.count(),
            'debug_repuestos_count': repuestos.count(),
                    # Debug values
        'debug_repuestos_values': [(r.codigo, r.nombre, r.cantidad, float(r.precio_unitario), float(r.precio_unitario * r.cantidad)) for r in repuestos],
        'debug_servicios_values': [(s.nombre, s.cantidad, float(s.precio_unitario), float(s.precio_unitario * s.cantidad)) for s in servicios],
        'debug_otros_values': [(o.nombre, o.cantidad, float(o.precio_cliente), float(o.precio_cliente * o.cantidad)) for o in otros_servicios],
        # Debug totals
        'debug_subtotal_repuestos': float(subtotal_repuestos),
        'debug_subtotal_servicios': float(subtotal_servicios),
        'debug_subtotal_otros': float(subtotal_otros_servicios),
        'debug_subtotal': float(subtotal),
        'debug_iva': float(iva),
        'debug_total': float(total),
        })
        return context


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
