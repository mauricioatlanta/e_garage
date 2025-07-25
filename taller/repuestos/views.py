from taller.models.empresa import Empresa
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from taller.models.repuesto import Repuesto
import logging

# Configurar logger
logger = logging.getLogger(__name__)

@login_required
def dashboard_repuestos(request):
    return render(request, 'taller/repuestos/dashboard.html')

@login_required
def lista_repuestos(request):
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        # Si no existe empresa, crear una por defecto
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    q = request.GET.get('q', '').strip()
    tienda = request.GET.get('tienda', '').strip()
    
    # Filtrar repuestos por empresa del usuario
    repuestos = Repuesto.objects.select_related('tienda').filter(empresa=empresa)
    
    if q:
        repuestos = repuestos.filter(
            Q(nombre_repuesto__icontains=q) |
            Q(part_number__icontains=q)
        )
    if tienda:
        repuestos = repuestos.filter(tienda__id=tienda)
    repuestos = repuestos.order_by('nombre_repuesto')
    
    # Para el filtro de tiendas - solo mostrar tiendas de la empresa del usuario
    tiendas = Repuesto.objects.filter(empresa=empresa).values_list('tienda__id', 'tienda__nombre').distinct().order_by('tienda__nombre')
    
    return render(request, 'taller/repuestos/listar_repuestos.html', {
        'repuestos': repuestos,
        'q': q,
        'tienda': tienda,
        'tiendas': tiendas,
    })

@login_required
def crear_repuesto(request):
    from taller.models.tienda import Tienda
    from taller.forms.repuesto import RepuestoForm
    from django.contrib import messages
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"crear_repuesto - Método: {request.method}")
    logger.info(f"Usuario autenticado: {request.user.is_authenticated}")
    
    if request.method == 'POST':
        logger.info(f"POST data: {request.POST}")
        form = RepuestoForm(request.POST)
        
        logger.info(f"Formulario válido: {form.is_valid()}")
        if not form.is_valid():
            logger.error(f"Errores del formulario: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en {field}: {error}")
            # Volver a mostrar el formulario con errores
            try:
                empresa = request.user.empresa
            except AttributeError:
                from taller.models.empresa import Empresa
                empresa, created = Empresa.objects.get_or_create(
                    user=request.user,
                    defaults={'nombre_taller': f'Taller de {request.user.username}'}
                )
            tiendas = Tienda.objects.filter(empresa=empresa).order_by('nombre')
            return render(request, 'taller/repuestos/agregar_repuesto.html', {
                'form': form,
                'tiendas': tiendas
            })
        
        try:
            # Obtener empresa del usuario
            # Verificar si el usuario tiene una empresa asociada
            try:
                empresa = request.user.empresa  # related_name desde el modelo Empresa
                logger.info(f"Empresa del usuario: {empresa}")
            except AttributeError:
                # Si no existe la relación, crear/obtener empresa para el usuario
                from taller.models.empresa import Empresa
                empresa, created = Empresa.objects.get_or_create(
                    user=request.user,
                    defaults={'nombre_taller': f'Taller de {request.user.username}'}
                )
                logger.info(f"Empresa {'creada' if created else 'encontrada'}: {empresa}")
            
            repuesto = form.save(commit=False)
            repuesto.empresa = empresa
            repuesto.save()
            
            logger.info(f"Repuesto creado: {repuesto} con ID: {repuesto.id}")
            messages.success(request, f"Repuesto '{repuesto.nombre_repuesto}' creado exitosamente.")
            return redirect('repuestos:lista_repuestos')
            
        except Exception as e:
            messages.error(request, f"Error al guardar: {str(e)}")
            logger.error(f"Error al guardar repuesto: {str(e)}")
            return redirect(request.path)
    else:
        # Crear siempre un formulario completamente nuevo y vacío
        form = RepuestoForm()
        logger.info("Creando formulario nuevo (GET)")
    
    # Obtener empresa del usuario para filtrar tiendas
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    tiendas = Tienda.objects.filter(empresa=empresa).order_by('nombre')
    logger.info(f"Número de tiendas: {tiendas.count()}")
    
    return render(request, 'taller/repuestos/agregar_repuesto.html', {
        'form': form,
        'tiendas': tiendas
    })

@login_required
def editar_repuesto(request, repuesto_id):
    """
    Vista para editar un repuesto existente.
    GET: Muestra el formulario con los datos del repuesto
    POST: Actualiza el repuesto
    """
    from taller.forms.repuesto import RepuestoForm
    from taller.models.tienda import Tienda
    
    logger.info(f"Usuario {request.user.username} accediendo a editar repuesto ID: {repuesto_id}")
    
    try:
        # Obtener el repuesto
        repuesto = get_object_or_404(Repuesto, pk=repuesto_id)
        
        # Verificar que el repuesto pertenece a la empresa del usuario
        try:
            empresa = request.user.empresa
        except AttributeError:
            logger.error(f"Usuario {request.user.username} no tiene empresa asociada")
            messages.error(request, 'Tu usuario no tiene una empresa asociada.')
            return redirect('repuestos:lista_repuestos')
        
        if repuesto.empresa != empresa:
            logger.warning(f"Usuario {request.user.username} intentó editar repuesto de otra empresa")
            messages.error(request, 'No tienes permisos para editar este repuesto.')
            return redirect('repuestos:lista_repuestos')
        
        # Obtener todas las tiendas de la empresa para el select
        tiendas = Tienda.objects.filter(empresa=empresa).order_by('nombre')
        
        if request.method == 'POST':
            form = RepuestoForm(request.POST, instance=repuesto)
            
            if form.is_valid():
                try:
                    repuesto_actualizado = form.save(commit=False)
                    repuesto_actualizado.empresa = empresa
                    repuesto_actualizado.save()
                    
                    logger.info(f"Repuesto {repuesto_id} actualizado exitosamente por {request.user.username}")
                    messages.success(request, f"Repuesto '{repuesto_actualizado.nombre_repuesto}' actualizado exitosamente.")
                    return redirect('repuestos:lista_repuestos')
                    
                except Exception as e:
                    logger.error(f"Error al actualizar repuesto {repuesto_id}: {str(e)}")
                    messages.error(request, f"Error al actualizar el repuesto: {str(e)}")
            else:
                logger.warning(f"Formulario inválido al editar repuesto {repuesto_id}: {form.errors}")
                messages.error(request, "Por favor, corrige los errores en el formulario.")
        else:
            # GET: Crear formulario con datos existentes
            form = RepuestoForm(instance=repuesto)
        
        context = {
            'form': form,
            'tiendas': tiendas,
            'repuesto': repuesto,
            'repuesto_id': repuesto_id
        }
        return render(request, 'taller/repuestos/editar_repuesto.html', context)
        
    except Exception as e:
        logger.error(f"Error inesperado al editar repuesto {repuesto_id}: {str(e)}")
        messages.error(request, 'Ocurrió un error inesperado al acceder al repuesto.')
        return redirect('repuestos:lista_repuestos')

@login_required
def eliminar_repuesto(request, repuesto_id):
    """
    Vista para eliminar un repuesto.
    GET: Muestra la página de confirmación
    POST: Elimina el repuesto
    """
    logger.info(f"Usuario {request.user.username} accediendo a eliminar repuesto ID: {repuesto_id}")
    
    try:
        # Obtener el repuesto
        repuesto = get_object_or_404(Repuesto, pk=repuesto_id)
        
        # Verificar que el repuesto pertenece a la empresa del usuario
        try:
            empresa = request.user.empresa
        except AttributeError:
            logger.error(f"Usuario {request.user.username} no tiene empresa asociada")
            messages.error(request, 'Tu usuario no tiene una empresa asociada.')
            return redirect('/repuestos/')
        
        if repuesto.empresa != empresa:
            logger.warning(f"Usuario {request.user.username} intentó eliminar repuesto de otra empresa")
            messages.error(request, 'No tienes permisos para eliminar este repuesto.')
            return redirect('/repuestos/')
        
        if request.method == 'POST':
            # Eliminar el repuesto
            repuesto_nombre = repuesto.nombre_repuesto
            repuesto.delete()
            
            logger.info(f"Repuesto '{repuesto_nombre}' eliminado exitosamente por {request.user.username}")
            messages.success(request, f"Repuesto '{repuesto_nombre}' eliminado exitosamente.")
            return redirect('/repuestos/')
        
        # GET: Mostrar página de confirmación
        context = {
            'repuesto': repuesto,
            'repuesto_id': repuesto_id
        }
        return render(request, 'taller/repuestos/eliminar_repuesto.html', context)
        
    except Repuesto.DoesNotExist:
        logger.error(f"Repuesto con ID {repuesto_id} no existe")
        messages.error(request, 'El repuesto que intentas eliminar no existe.')
        context = {
            'repuesto': None,
            'repuesto_id': repuesto_id
        }
        return render(request, 'taller/repuestos/eliminar_repuesto.html', context)
    
    except Exception as e:
        logger.error(f"Error inesperado al eliminar repuesto {repuesto_id}: {str(e)}")
        messages.error(request, 'Ocurrió un error inesperado al eliminar el repuesto.')
        return redirect('/repuestos/')

def validar_part_number(request):
    # Simulación de validación
    return render(request, 'taller/repuestos/validar_part_number.html')

@login_required
def api_autocomplete_repuesto(request):
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    q = request.GET.get('q', '').strip()
    # Filtrar repuestos por empresa del usuario
    repuestos = Repuesto.objects.filter(empresa=empresa)  # 🔒 FILTRO EMPRESA
    if q:
        repuestos = repuestos.filter(
            Q(nombre_repuesto__icontains=q) |
            Q(part_number__icontains=q)
        )
    repuestos = repuestos.order_by('nombre_repuesto')[:10]
    data = [
        {
            'part_number': r.part_number,
            'nombre_repuesto': r.nombre_repuesto,
            'precio_venta': float(r.precio_venta),
        }
        for r in repuestos
    ]
    return JsonResponse({'results': data})

@login_required
def crear_tienda(request):
    """Vista para crear una nueva tienda via AJAX"""
    from taller.models.tienda import Tienda
    
    if request.method == 'POST':
        try:
            # Obtener la empresa del usuario
            empresa = request.user.empresa
            
            nombre = request.POST.get('nombre', '').strip()
            direccion = request.POST.get('direccion', '').strip()
            telefono = request.POST.get('telefono', '').strip()
            
            if not nombre:
                return JsonResponse({
                    'success': False,
                    'error': 'El nombre de la tienda es requerido'
                })
            
            # Verificar que no exista otra tienda con el mismo nombre en la empresa
            if Tienda.objects.filter(empresa=empresa, nombre=nombre).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Ya existe una tienda con ese nombre'
                })
            
            # Crear la tienda
            tienda = Tienda.objects.create(
                empresa=empresa,
                nombre=nombre,
                direccion=direccion,
                telefono=telefono
            )
            
            return JsonResponse({
                'success': True,
                'tienda': {
                    'id': tienda.id,
                    'nombre': tienda.nombre
                }
            })
            
        except Exception as e:
            logger.error(f"Error al crear tienda: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error interno del servidor'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido'
    })
