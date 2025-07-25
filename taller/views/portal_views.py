"""
🌐 VIEWS DEL PORTAL DE CLIENTES
==============================

Views para el portal web donde los clientes pueden:
- Iniciar sesión y ver sus documentos
- Solicitar presupuestos
- Revisar historial de servicios
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import json

from taller.models.cliente import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.documento import Documento
from taller.models.portal_cliente import (
    ClienteUsuario, SolicitudPresupuesto, 
    PortalConfiguracion, AccesoPortal
)

def portal_login(request):
    """Vista de login del portal de clientes"""
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            # Buscar cliente por email
            cliente = Cliente.objects.filter(email_cliente=email).first()
            if not cliente:
                messages.error(request, 'Cliente no encontrado')
                return render(request, 'portal/login.html')
            
            # Verificar si existe usuario del portal
            cliente_usuario = ClienteUsuario.objects.filter(cliente=cliente).first()
            if not cliente_usuario:
                messages.error(request, 'Acceso al portal no configurado')
                return render(request, 'portal/login.html')
            
            # Autenticar
            user = authenticate(request, username=cliente_usuario.user.username, password=password)
            if user:
                login(request, user)
                
                # Registrar acceso
                AccesoPortal.objects.create(
                    cliente_usuario=cliente_usuario,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    pagina_visitada='login',
                    accion_realizada='login_exitoso'
                )
                
                # Actualizar último acceso
                cliente_usuario.ultimo_acceso = timezone.now()
                cliente_usuario.save()
                
                return redirect('portal_dashboard')
            else:
                messages.error(request, 'Credenciales incorrectas')
                
        except Exception as e:
            messages.error(request, f'Error en el sistema: {str(e)}')
    
    return render(request, 'portal/login.html')

@login_required
def portal_dashboard(request):
    """Dashboard principal del portal de clientes"""
    
    try:
        cliente_usuario = ClienteUsuario.objects.get(user=request.user)
        cliente = cliente_usuario.cliente
        
        # Obtener configuración del portal
        portal_config = PortalConfiguracion.objects.filter(empresa=cliente.empresa).first()
        
        # Estadísticas básicas
        vehiculos = Vehiculo.objects.filter(id_cliente=cliente)
        documentos_recientes = Documento.objects.filter(
            id_cliente=cliente
        ).order_by('-fecha_documento')[:5]
        
        solicitudes_pendientes = SolicitudPresupuesto.objects.filter(
            cliente=cliente,
            estado__in=['PENDIENTE', 'EN_REVISION']
        ).count()
        
        context = {
            'cliente': cliente,
            'vehiculos': vehiculos,
            'documentos_recientes': documentos_recientes,
            'solicitudes_pendientes': solicitudes_pendientes,
            'portal_config': portal_config,
        }
        
        # Registrar acceso
        AccesoPortal.objects.create(
            cliente_usuario=cliente_usuario,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            pagina_visitada='dashboard',
            accion_realizada='vista_dashboard'
        )
        
        return render(request, 'portal/dashboard.html', context)
        
    except ClienteUsuario.DoesNotExist:
        messages.error(request, 'Acceso no autorizado')
        return redirect('portal_login')

@login_required
def portal_documentos(request):
    """Vista de documentos del cliente"""
    
    try:
        cliente_usuario = ClienteUsuario.objects.get(user=request.user)
        cliente = cliente_usuario.cliente
        
        # Filtros
        vehiculo_id = request.GET.get('vehiculo')
        tipo_doc = request.GET.get('tipo')
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        
        # Query base
        documentos = Documento.objects.filter(id_cliente=cliente)
        
        # Aplicar filtros
        if vehiculo_id:
            documentos = documentos.filter(id_vehiculo_id=vehiculo_id)
        if tipo_doc:
            documentos = documentos.filter(tipo_documento=tipo_doc)
        if fecha_desde:
            documentos = documentos.filter(fecha_documento__gte=fecha_desde)
        if fecha_hasta:
            documentos = documentos.filter(fecha_documento__lte=fecha_hasta)
        
        documentos = documentos.order_by('-fecha_documento')
        
        # Paginación
        paginator = Paginator(documentos, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Datos para filtros
        vehiculos = Vehiculo.objects.filter(id_cliente=cliente)
        tipos_documento = Documento.objects.filter(
            id_cliente=cliente
        ).values_list('tipo_documento', flat=True).distinct()
        
        context = {
            'cliente': cliente,
            'page_obj': page_obj,
            'vehiculos': vehiculos,
            'tipos_documento': tipos_documento,
            'filtros': {
                'vehiculo_id': vehiculo_id,
                'tipo_doc': tipo_doc,
                'fecha_desde': fecha_desde,
                'fecha_hasta': fecha_hasta,
            }
        }
        
        # Registrar acceso
        AccesoPortal.objects.create(
            cliente_usuario=cliente_usuario,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            pagina_visitada='documentos',
            accion_realizada='vista_documentos'
        )
        
        return render(request, 'portal/documentos.html', context)
        
    except ClienteUsuario.DoesNotExist:
        messages.error(request, 'Acceso no autorizado')
        return redirect('portal_login')

@login_required
def portal_solicitar_presupuesto(request):
    """Vista para solicitar presupuestos"""
    
    try:
        cliente_usuario = ClienteUsuario.objects.get(user=request.user)
        cliente = cliente_usuario.cliente
        
        if request.method == 'POST':
            # Procesar solicitud
            vehiculo_id = request.POST.get('vehiculo')
            titulo = request.POST.get('titulo')
            descripcion = request.POST.get('descripcion')
            prioridad = request.POST.get('prioridad', 'MEDIA')
            fecha_deseada = request.POST.get('fecha_deseada')
            
            try:
                vehiculo = Vehiculo.objects.get(id=vehiculo_id, id_cliente=cliente)
                
                solicitud = SolicitudPresupuesto.objects.create(
                    empresa=cliente.empresa,
                    cliente=cliente,
                    vehiculo=vehiculo,
                    titulo=titulo,
                    descripcion=descripcion,
                    prioridad=prioridad,
                    fecha_deseada=fecha_deseada if fecha_deseada else None
                )
                
                messages.success(request, f'Solicitud {solicitud.numero_solicitud} creada exitosamente')
                
                # Registrar acceso
                AccesoPortal.objects.create(
                    cliente_usuario=cliente_usuario,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    pagina_visitada='solicitar_presupuesto',
                    accion_realizada=f'crear_solicitud_{solicitud.numero_solicitud}'
                )
                
                return redirect('portal_mis_solicitudes')
                
            except Vehiculo.DoesNotExist:
                messages.error(request, 'Vehículo no válido')
            except Exception as e:
                messages.error(request, f'Error al crear solicitud: {str(e)}')
        
        # Obtener vehículos del cliente
        vehiculos = Vehiculo.objects.filter(id_cliente=cliente)
        
        context = {
            'cliente': cliente,
            'vehiculos': vehiculos,
        }
        
        return render(request, 'portal/solicitar_presupuesto.html', context)
        
    except ClienteUsuario.DoesNotExist:
        messages.error(request, 'Acceso no autorizado')
        return redirect('portal_login')

@login_required
def portal_mis_solicitudes(request):
    """Vista de solicitudes del cliente"""
    
    try:
        cliente_usuario = ClienteUsuario.objects.get(user=request.user)
        cliente = cliente_usuario.cliente
        
        # Obtener solicitudes
        solicitudes = SolicitudPresupuesto.objects.filter(
            cliente=cliente
        ).order_by('-created_at')
        
        # Paginación
        paginator = Paginator(solicitudes, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'cliente': cliente,
            'page_obj': page_obj,
        }
        
        # Registrar acceso
        AccesoPortal.objects.create(
            cliente_usuario=cliente_usuario,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            pagina_visitada='mis_solicitudes',
            accion_realizada='vista_solicitudes'
        )
        
        return render(request, 'portal/mis_solicitudes.html', context)
        
    except ClienteUsuario.DoesNotExist:
        messages.error(request, 'Acceso no autorizado')
        return redirect('portal_login')

@login_required
def portal_vehiculos(request):
    """Vista de vehículos del cliente"""
    
    try:
        cliente_usuario = ClienteUsuario.objects.get(user=request.user)
        cliente = cliente_usuario.cliente
        
        vehiculos = Vehiculo.objects.filter(id_cliente=cliente)
        
        context = {
            'cliente': cliente,
            'vehiculos': vehiculos,
        }
        
        # Registrar acceso
        AccesoPortal.objects.create(
            cliente_usuario=cliente_usuario,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            pagina_visitada='vehiculos',
            accion_realizada='vista_vehiculos'
        )
        
        return render(request, 'portal/vehiculos.html', context)
        
    except ClienteUsuario.DoesNotExist:
        messages.error(request, 'Acceso no autorizado')
        return redirect('portal_login')

def portal_logout(request):
    """Logout del portal"""
    logout(request)
    messages.info(request, 'Sesión cerrada exitosamente')
    return redirect('portal_login')

# AJAX Views
@login_required
def ajax_detalle_documento(request, documento_id):
    """Vista AJAX para obtener detalles de un documento"""
    
    try:
        cliente_usuario = ClienteUsuario.objects.get(user=request.user)
        cliente = cliente_usuario.cliente
        
        documento = get_object_or_404(Documento, id=documento_id, id_cliente=cliente)
        
        data = {
            'numero': documento.numero_documento,
            'fecha': documento.fecha_documento.strftime('%d/%m/%Y'),
            'tipo': documento.tipo_documento,
            'vehiculo': f"{documento.id_vehiculo.marca} {documento.id_vehiculo.modelo}",
            'total': float(documento.total),
            'observaciones': documento.observaciones,
        }
        
        return JsonResponse(data)
        
    except ClienteUsuario.DoesNotExist:
        return JsonResponse({'error': 'Acceso no autorizado'}, status=403)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
