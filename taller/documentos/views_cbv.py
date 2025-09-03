from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from core.views import TenantViewMixin
from taller.mixins import CountryLangTemplateMixin  # Agregar import del mixin
from .models import Documento
from .forms import DocumentoForm

class DocumentoListView(LoginRequiredMixin, TenantViewMixin, ListView):
    model = Documento
    select_related_fields = ("cliente","vehiculo", "tecnico_responsable")
    prefetch_related_fields = ("lineas_repuesto__repuesto", "lineas_servicio__servicio", "lineas_otro_servicio")
    paginate_by = 50
    ordering = ("-fecha_emision","-id")
    
    def get_queryset(self):
        qs = super().get_queryset()
        # Optimizar consultas
        qs = qs.select_related("cliente", "vehiculo", "tecnico_responsable")
        qs = qs.prefetch_related(
            "lineas_repuesto__repuesto", 
            "lineas_servicio__servicio", 
            "lineas_otro_servicio"
        )
        
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

class DocumentoDetailView(LoginRequiredMixin, TenantViewMixin, CountryLangTemplateMixin, DetailView):
    model = Documento
    base_template_name = "documentos/ver_documento_nuevo.html"
    select_related_fields = ("cliente", "vehiculo", "tecnico_responsable")
    prefetch_related_fields = ("lineas_repuesto__repuesto", "lineas_servicio__servicio", "lineas_otro_servicio")
    
    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)
    
    def get_queryset(self):
        """Optimizar consultas con select_related y prefetch_related"""
        qs = super().get_queryset()
        qs = qs.select_related("cliente", "vehiculo", "tecnico_responsable")
        qs = qs.prefetch_related(
            "lineas_repuesto__repuesto", 
            "lineas_servicio__servicio", 
            "lineas_otro_servicio"
        )
        return qs
    
    def get_context_data(self, **kwargs):
        """Agregar el objeto como 'documento' al contexto y calcular totales"""
        ctx = super().get_context_data(**kwargs)
        doc = self.object
        ctx['documento'] = doc

        # Sumas servidor usando aggregates (sin depender de JS)
        sum_rep = doc.lineas_repuesto.aggregate(
            total=Sum(ExpressionWrapper(F('cantidad') * F('precio_unitario'),
                                        output_field=DecimalField(max_digits=12, decimal_places=2)))
        )['total'] or 0

        sum_serv = doc.lineas_servicio.aggregate(
            total=Sum('precio_unitario')
        )['total'] or 0

        sum_otros = doc.lineas_otro_servicio.aggregate(
            total=Sum('precio_cliente')
        )['total'] or 0

        subtotal = (sum_rep or 0) + (sum_serv or 0) + (sum_otros or 0)

        # País y reglas (del context processor que ya tienes)
        tax_base = ctx.get("doc_tax_base", "parts_only")      # "parts_only" (CL) | "subtotal" (US)
        rate = float(ctx.get("doc_tax_rate", 0.0))            # 0.19 CL | ej. 0.08 US
        base = sum_rep if tax_base == "parts_only" else subtotal
        tax = round(base * rate, 2) if getattr(doc, "incluir_iva", True) else 0
        total = subtotal + tax

        # Datos detallados para el template
        repuestos = []
        for lr in doc.lineas_repuesto.all().select_related('repuesto'):
            repuestos.append({
                "codigo": lr.repuesto.part_number if getattr(lr, "repuesto", None) else "",
                "nombre": lr.nombre,
                "cantidad": lr.cantidad,
                "precio": float(lr.precio_unitario),
                "total": float(lr.cantidad * lr.precio_unitario),
            })

        servicios = []
        for ls in doc.lineas_servicio.all().select_related('servicio'):
            servicios.append({
                "nombre": ls.nombre,
                "precio": float(ls.precio_unitario),
            })

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

        ctx.update({
            "repuestos": repuestos,
            "servicios": servicios,
            "otros_servicios": otros,
            "subtotal_repuestos": sum_rep,
            "subtotal_servicios": sum_serv,
            "subtotal_otros": sum_otros,
            "subtotal": subtotal,
            "iva": tax,
            "total": total,
        })
        return ctx

class DocumentoCreateView(LoginRequiredMixin, TenantViewMixin, CountryLangTemplateMixin, CreateView):
    model = Documento
    form_class = DocumentoForm
    base_template_name = "documentos/crear_documento.html"
    
    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)
    
    def get_success_url(self):
        """Redirigir al listado de documentos después de crear"""
        from django.urls import reverse
        return reverse('documentos:lista_documentos')
    
    def form_valid(self, form):
        """Agregar mensaje de éxito al crear el documento y procesar items dinámicos"""
        from django.contrib import messages
        
        # Guardar el documento primero
        response = super().form_valid(form)
        
        # Procesar items dinámicos después de guardar
        self.procesar_items_dinamicos(form)
        
        messages.success(
            self.request, 
            f"✅ Documento {self.object.tipo}-{self.object.numero} creado exitosamente"
        )
        return response
    
    def procesar_items_dinamicos(self, form):
        """Procesa los campos dinámicos de repuestos, servicios y otros servicios"""
        documento = form.instance
        
        # Procesar repuestos dinámicos
        self.procesar_repuestos_dinamicos(documento)
        
        # Procesar servicios dinámicos
        self.procesar_servicios_dinamicos(documento)
        
        # Procesar otros servicios dinámicos
        self.procesar_otros_servicios_dinamicos(documento)
    
    def procesar_repuestos_dinamicos(self, documento):
        """Procesa los repuestos agregados dinámicamente"""
        from taller.models.lineas_documento import LineaRepuesto
        
        codigos = self.request.POST.getlist('repuesto_codigo[]')
        nombres = self.request.POST.getlist('repuesto_nombre[]')
        cantidades = self.request.POST.getlist('repuesto_cantidad[]')
        precios = self.request.POST.getlist('repuesto_precio[]')
        
        for i, (codigo, nombre, cantidad, precio) in enumerate(zip(codigos, nombres, cantidades, precios)):
            if nombre.strip():  # Solo crear si hay nombre
                LineaRepuesto.objects.create(
                    documento=documento,
                    nombre=nombre.strip(),
                    cantidad=int(cantidad) if cantidad else 1,
                    precio_unitario=float(precio) if precio else 0.0
                )
    
    def procesar_servicios_dinamicos(self, documento):
        """Procesa los servicios agregados dinámicamente"""
        from taller.models.lineas_documento import LineaServicio
        
        nombres = self.request.POST.getlist('servicio_nombre[]')
        precios = self.request.POST.getlist('servicio_precio[]')
        
        for nombre, precio in zip(nombres, precios):
            if nombre.strip():  # Solo crear si hay nombre
                LineaServicio.objects.create(
                    documento=documento,
                    nombre=nombre.strip(),
                    cantidad=1,
                    precio_unitario=float(precio) if precio else 0.0
                )
    
    def procesar_otros_servicios_dinamicos(self, documento):
        """Procesa los otros servicios agregados dinámicamente"""
        from taller.models.lineas_documento import LineaOtroServicio
        
        servicios = self.request.POST.getlist('otro_servicio[]')
        empresas = self.request.POST.getlist('otro_empresa[]')
        costos = self.request.POST.getlist('otro_costo[]')
        precios = self.request.POST.getlist('otro_precio[]')
        
        for servicio, empresa, costo, precio in zip(servicios, empresas, costos, precios):
            if servicio.strip():  # Solo crear si hay nombre de servicio
                LineaOtroServicio.objects.create(
                    documento=documento,
                    nombre=servicio.strip(),
                    empresa_externa=empresa.strip() if empresa else '',
                    cantidad=1,
                    costo_interno=float(costo) if costo else 0.0,
                    precio_cliente=float(precio) if precio else 0.0
                )

class DocumentoUpdateView(LoginRequiredMixin, TenantViewMixin, CountryLangTemplateMixin, UpdateView):
    model = Documento
    form_class = DocumentoForm
    base_template_name = "documentos/editar_documento_nuevo.html"
    select_related_fields = ("cliente", "vehiculo", "tecnico_responsable")
    prefetch_related_fields = ("lineas_repuesto__repuesto", "lineas_servicio__servicio", "lineas_otro_servicio")
    
    def render_to_response(self, context, **response_kwargs):
        return self.render_country_lang(self.request, context)
    
    def get_queryset(self):
        """Optimizar consultas con select_related y prefetch_related"""
        qs = super().get_queryset()
        qs = qs.select_related("cliente", "vehiculo", "tecnico_responsable")
        qs = qs.prefetch_related(
            "lineas_repuesto__repuesto", 
            "lineas_servicio__servicio", 
            "lineas_otro_servicio"
        )
        return qs
    
    def get_success_url(self):
        """Redirigir al listado de documentos después de editar"""
        from django.urls import reverse
        return reverse('documentos:lista_documentos')
    
    def form_valid(self, form):
        """Agregar mensaje de éxito al guardar el documento y procesar items dinámicos"""
        from django.contrib import messages
        
        # Procesar items dinámicos antes de guardar
        self.procesar_items_dinamicos(form)
        
        response = super().form_valid(form)
        messages.success(
            self.request, 
            f"✅ Documento {self.object.tipo}-{self.object.numero} actualizado exitosamente"
        )
        return response
    
    def procesar_items_dinamicos(self, form):
        """Procesa los campos dinámicos de repuestos, servicios y otros servicios"""
        documento = form.instance
        
        # Limpiar líneas existentes
        documento.lineas_repuesto.all().delete()
        documento.lineas_servicio.all().delete()
        documento.lineas_otro_servicio.all().delete()
        
        # Procesar repuestos dinámicos
        self.procesar_repuestos_dinamicos(documento)
        
        # Procesar servicios dinámicos
        self.procesar_servicios_dinamicos(documento)
        
        # Procesar otros servicios dinámicos
        self.procesar_otros_servicios_dinamicos(documento)
    
    def procesar_repuestos_dinamicos(self, documento):
        """Procesa los repuestos agregados dinámicamente"""
        from taller.models.lineas_documento import LineaRepuesto
        
        codigos = self.request.POST.getlist('repuesto_codigo[]')
        nombres = self.request.POST.getlist('repuesto_nombre[]')
        cantidades = self.request.POST.getlist('repuesto_cantidad[]')
        precios = self.request.POST.getlist('repuesto_precio[]')
        
        for i, (codigo, nombre, cantidad, precio) in enumerate(zip(codigos, nombres, cantidades, precios)):
            if nombre.strip():  # Solo crear si hay nombre
                LineaRepuesto.objects.create(
                    documento=documento,
                    nombre=nombre.strip(),
                    cantidad=int(cantidad) if cantidad else 1,
                    precio_unitario=float(precio) if precio else 0.0,
                    # part_number=codigo.strip() if codigo else None
                )
    
    def procesar_servicios_dinamicos(self, documento):
        """Procesa los servicios agregados dinámicamente"""
        from taller.models.lineas_documento import LineaServicio
        
        nombres = self.request.POST.getlist('servicio_nombre[]')
        precios = self.request.POST.getlist('servicio_precio[]')
        
        for nombre, precio in zip(nombres, precios):
            if nombre.strip():  # Solo crear si hay nombre
                LineaServicio.objects.create(
                    documento=documento,
                    nombre=nombre.strip(),
                    cantidad=1,
                    precio_unitario=float(precio) if precio else 0.0
                )
    
    def procesar_otros_servicios_dinamicos(self, documento):
        """Procesa los otros servicios agregados dinámicamente"""
        from taller.models.lineas_documento import LineaOtroServicio
        
        servicios = self.request.POST.getlist('otro_servicio[]')
        empresas = self.request.POST.getlist('otro_empresa[]')
        costos = self.request.POST.getlist('otro_costo[]')
        precios = self.request.POST.getlist('otro_precio[]')
        
        for servicio, empresa, costo, precio in zip(servicios, empresas, costos, precios):
            if servicio.strip():  # Solo crear si hay nombre de servicio
                LineaOtroServicio.objects.create(
                    documento=documento,
                    nombre=servicio.strip(),
                    empresa_externa=empresa.strip() if empresa else '',
                    cantidad=1,
                    costo_interno=float(costo) if costo else 0.0,
                    precio_cliente=float(precio) if precio else 0.0
                )
    
    def get_object(self, queryset=None):
        """Filtrar por empresa del usuario"""
        obj = super().get_object(queryset)
        # Verificar que el documento pertenece a la empresa del usuario
        try:
            empresa = self.request.user.empresa
            if obj.empresa != empresa:
                from django.http import Http404
                raise Http404("Documento no encontrado")
        except AttributeError:
            # Usuario sin empresa - crear una
            from taller.models.empresa import Empresa
            empresa, created = Empresa.objects.get_or_create(
                user=self.request.user,
                defaults={'nombre_taller': f'Taller de {self.request.user.username}'}
            )
            if obj.empresa != empresa:
                from django.http import Http404
                raise Http404("Documento no encontrado")
        return obj
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Usar la empresa del middleware
        empresa = getattr(self.request, 'empresa', None)
        if empresa:
            kwargs['empresa'] = empresa
        return kwargs
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        doc = self.object

        # Sumas servidor usando aggregates (sin depender de JS)
        sum_rep = doc.lineas_repuesto.aggregate(
            total=Sum(ExpressionWrapper(F('cantidad') * F('precio_unitario'),
                                        output_field=DecimalField(max_digits=12, decimal_places=2)))
        )['total'] or 0

        sum_serv = doc.lineas_servicio.aggregate(
            total=Sum('precio_unitario')
        )['total'] or 0

        sum_otros = doc.lineas_otro_servicio.aggregate(
            total=Sum('precio_cliente')
        )['total'] or 0

        subtotal = (sum_rep or 0) + (sum_serv or 0) + (sum_otros or 0)

        # País y reglas (del context processor que ya tienes)
        tax_base = ctx.get("doc_tax_base", "parts_only")      # "parts_only" (CL) | "subtotal" (US)
        rate = float(ctx.get("doc_tax_rate", 0.0))            # 0.19 CL | ej. 0.08 US
        base = sum_rep if tax_base == "parts_only" else subtotal
        tax = round(base * rate, 2) if getattr(doc, "incluir_iva", True) else 0
        total = subtotal + tax

        # Datos detallados para el template (opcional, para tablas)
        repuestos = []
        for lr in doc.lineas_repuesto.all().select_related():
            repuestos.append({
                "codigo": lr.repuesto.part_number if getattr(lr, "repuesto", None) else "",
                "nombre": lr.nombre,
                "cantidad": lr.cantidad,
                "precio": float(lr.precio_unitario),
                "total": float(lr.cantidad * lr.precio_unitario),
            })

        servicios = []
        for ls in doc.lineas_servicio.all().select_related():
            servicios.append({
                "nombre": ls.nombre,
                "precio": float(ls.precio_unitario),
            })

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

        ctx.update({
            "repuestos": repuestos,
            "servicios": servicios,
            "otros_servicios": otros,
            "subtotal_repuestos": sum_rep,
            "subtotal_servicios": sum_serv,
            "subtotal_otros": sum_otros,
            "subtotal": subtotal,
            "iva": tax,            # en US lo mostrarás como Sales Tax (usa tu label dinámico)
            "total": total,
        })
        return ctx
