from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.db.models import Q, Count
from .models import Servicio, CategoriaServicio, SubcategoriaServicio

# Menú principal de servicios con diseño moderno
def servicios_menu(request):
    # Obtener empresa del usuario
    empresa = getattr(request.user, 'empresa', None)
    
    # Obtener servicios con filtros básicos
    servicios = Servicio.objects.filter(empresa=empresa) if empresa else Servicio.objects.none()
    categorias = CategoriaServicio.objects.all()
    subcategorias = SubcategoriaServicio.objects.all()
    
    # Estadísticas para el dashboard
    stats = {
        'total_servicios': servicios.count(),
        'total_categorias': categorias.count(),
        'total_subcategorias': subcategorias.count(),
    }
    
    context = {
        'servicios': servicios[:50],  # Limitar para performance inicial
        'categorias': categorias,
        'subcategorias': subcategorias,
        'stats': stats,
        'empresa': empresa,
    }
    
    return render(request, 'servicios/servicios_menu.html', context)

# API para búsqueda en tiempo real
def buscar_servicios_api(request):
    query = request.GET.get('q', '').strip()
    categoria_id = request.GET.get('categoria', '')
    
    # Obtener empresa del usuario
    empresa = getattr(request.user, 'empresa', None)
    
    servicios = Servicio.objects.filter(empresa=empresa) if empresa else Servicio.objects.none()
    
    # Aplicar filtros de búsqueda
    if query:
        servicios = servicios.filter(
            Q(nombre__icontains=query) |
            Q(categoria__names__label__icontains=query) |
            Q(subcategoria__names__label__icontains=query)
        ).distinct()
    
    if categoria_id:
        servicios = servicios.filter(categoria_id=categoria_id)
    
    # Preparar datos para JSON
    data = []
    for servicio in servicios[:20]:  # Limitar resultados
        data.append({
            'pk': servicio.pk,
            'nombre': servicio.nombre,
            'categoria': servicio.categoria.get_label() if servicio.categoria else '',
            'subcategoria': servicio.subcategoria.get_label() if servicio.subcategoria else '',
        })
    
    return JsonResponse({
        'servicios': data,
        'total': servicios.count(),
    })

# Menú de otros servicios (placeholder)
def otros_servicios_menu(request):
    """Vista para el menú de otros servicios (servicios externos) con búsqueda inteligente"""
    from taller.servicios.models import ServicioExterno, CategoriaServicio
    
    # Obtener empresa del usuario
    empresa = getattr(request.user, 'empresa', None)
    if empresa:
        # Obtener servicios externos de la empresa
        otros_servicios = ServicioExterno.objects.filter(
            empresa=empresa, 
            activo=True
        ).select_related('categoria', 'subcategoria')
    else:
        otros_servicios = ServicioExterno.objects.none()
    
    # Obtener categorías para el formulario
    categorias = CategoriaServicio.objects.all()
    
    # Estadísticas
    stats = {
        'total_otros_servicios': otros_servicios.count(),
        'total_categorias': otros_servicios.values('categoria').distinct().count(),
        'total_subcategorias': otros_servicios.values('subcategoria').distinct().count(),
        'total_empresas_externas': otros_servicios.values('empresa_externa').distinct().count(),
    }
    
    context = {
        'otros_servicios': otros_servicios,
        'categorias': categorias,
        'stats': stats,
    }
    
    return render(request, 'servicios/otros_servicios_menu.html', context)

# Crear otro servicio
def crear_otro_servicio(request):
    """Vista para crear servicios externos"""
    from taller.servicios.models import ServicioExterno, CategoriaServicio
    from django.contrib import messages
    
    if request.method == 'POST':
        try:
            empresa = getattr(request.user, 'empresa', None)
            if not empresa:
                messages.error(request, "Usuario no tiene empresa asociada")
                return redirect('servicios:otros_servicios_menu')
            
            # Obtener datos del formulario
            nombre = request.POST.get('nombre')
            empresa_externa = request.POST.get('empresa_externa')
            categoria_id = request.POST.get('categoria')
            costo_taller = request.POST.get('costo_taller')
            precio_cliente = request.POST.get('precio_cliente')
            descripcion = request.POST.get('descripcion', '')
            tiempo_estimado = request.POST.get('tiempo_estimado', '')
            
            # Validaciones básicas
            if not all([nombre, empresa_externa, categoria_id, costo_taller, precio_cliente]):
                messages.error(request, "Todos los campos requeridos deben ser completados")
                return redirect('servicios:otros_servicios_menu')
            
            # Crear servicio externo
            categoria = CategoriaServicio.objects.get(id=categoria_id)
            servicio = ServicioExterno.objects.create(
                empresa=empresa,
                nombre=nombre,
                empresa_externa=empresa_externa,
                categoria=categoria,
                costo_taller=costo_taller,
                precio_cliente=precio_cliente,
                descripcion=descripcion,
                tiempo_estimado=tiempo_estimado,
                activo=True
            )
            
            messages.success(request, f"Servicio externo '{servicio.nombre}' creado exitosamente")
            
        except Exception as e:
            messages.error(request, f"Error al crear servicio externo: {str(e)}")
    
    return redirect('servicios:otros_servicios_menu')

import logging; log = logging.getLogger(__name__)
from .views_cbv import (
    ServicioListView, ServicioDetailView, ServicioCreateView, ServicioUpdateView
)

def lista_servicios(request, *args, **kwargs):
    log.info("FBV shim: lista_servicios")
    return ServicioListView.as_view()(request, *args, **kwargs)

def ver_servicio(request, *args, **kwargs):
    log.info("FBV shim: ver_servicio")
    return ServicioDetailView.as_view()(request, *args, **kwargs)

def crear_servicio(request, *args, **kwargs):
    log.info("FBV shim: crear_servicio")
    return ServicioCreateView.as_view()(request, *args, **kwargs)

def editar_servicio(request, *args, **kwargs):
    log.info("FBV shim: editar_servicio")
    return ServicioUpdateView.as_view()(request, *args, **kwargs)
