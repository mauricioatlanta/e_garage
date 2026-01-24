"""
Panel de Administración de Suscriptores
========================================

Vista administrativa para gestionar suscriptores:
- Listar suscriptores por país
- Ver status y días restantes
- Extender suscripciones
- Enviar notificaciones (email + WhatsApp)
"""

import logging
from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from taller.models.empresa import Empresa
from taller.models.suscripcion import Suscripcion
from taller.utils.country_config import COUNTRY_SETTINGS

logger = logging.getLogger(__name__)


@staff_member_required
def admin_suscriptores(request):
    """
    Panel principal de administración de suscriptores
    
    Filtros:
    - Por país (CL, US, MX, PE, CO, EC, BR, VE)
    - Por status (activa, vencida, trial)
    - Por días restantes (crítico < 5, bajo < 15, normal)
    """
    try:
        # Obtener filtros de la URL
        pais_filter = request.GET.get('pais', '')
        status_filter = request.GET.get('status', '')
        dias_filter = request.GET.get('dias', '')
        search_query = request.GET.get('search', '')
        
        # Obtener todas las empresas con sus usuarios y suscripciones
        # Suscripcion está relacionada con User, no directamente con Empresa
        # Filtrar empresas que tienen usuario para evitar errores
        try:
            empresas = Empresa.objects.select_related('user', 'user__suscripcion').filter(user__isnull=False)
        except Exception as e:
            logger.error(f"Error al obtener empresas: {e}", exc_info=True)
            # Si hay error con select_related, intentar sin él
            empresas = Empresa.objects.filter(user__isnull=False)
        
        # Aplicar filtros
        if pais_filter:
            empresas = empresas.filter(pais=pais_filter)
        
        if status_filter == 'activa':
            empresas = empresas.filter(suscripcion_activa=True)
        elif status_filter == 'vencida':
            empresas = empresas.filter(suscripcion_activa=False)
        elif status_filter == 'trial':
            empresas = empresas.filter(plan='trial')
        
        # Búsqueda por nombre de taller, email o teléfono (aplicar antes de convertir a lista)
        if search_query:
            empresas = empresas.filter(
                Q(nombre_taller__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(telefono__icontains=search_query)
            )
        
        # Convertir a lista para poder usar propiedades como estado_suscripcion
        # Agregar manejo de errores para empresas con datos inconsistentes
        empresas_list = []
        for empresa in empresas:
            try:
                # Verificar que la empresa tenga los datos necesarios
                _ = empresa.dias_restantes
                _ = empresa.estado_suscripcion
                empresas_list.append(empresa)
            except (AttributeError, TypeError, ValueError) as e:
                # Si hay un error con alguna empresa, loguear y continuar
                logger.warning(f"Error procesando empresa {empresa.id}: {e}")
                continue
        
        if dias_filter == 'critico':
            # Crítico: 1 día o menos (pero no vencido)
            empresas_list = [e for e in empresas_list if e.estado_suscripcion == 'critico']
        elif dias_filter == 'advertencia':
            # Advertencia: entre 1 y 5 días
            empresas_list = [e for e in empresas_list if e.estado_suscripcion == 'advertencia']
        elif dias_filter == 'vencido':
            # Vencido: debe_bloquear = True
            empresas_list = [e for e in empresas_list if e.estado_suscripcion == 'vencida']
        
        # Ordenar por días restantes (menos días primero)
        empresas = sorted(empresas_list, key=lambda e: e.dias_restantes if e.dias_restantes is not None else 0)
        
        # Paginación
        paginator = Paginator(empresas, 25)  # 25 por página (empresas ya es una lista ordenada)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Estadísticas generales
        total_empresas = Empresa.objects.count()
        empresas_activas = Empresa.objects.filter(suscripcion_activa=True).count()
        empresas_vencidas = Empresa.objects.filter(suscripcion_activa=False).count()
        
        # Estadísticas por país
        stats_por_pais = {}
        for codigo, config in COUNTRY_SETTINGS.items():
            stats_por_pais[codigo] = {
                'nombre': config.get('name', codigo),
                'total': Empresa.objects.filter(pais=codigo).count(),
                'activas': Empresa.objects.filter(pais=codigo, suscripcion_activa=True).count(),
                'vencidas': Empresa.objects.filter(pais=codigo, suscripcion_activa=False).count(),
            }
        
        # Empresas críticas (menos de 5 días) - solo empresas con usuario
        empresas_criticas = []
        for e in Empresa.objects.filter(user__isnull=False):
            try:
                dias = e.dias_restantes
                if dias is not None and 0 < dias < 5:
                    empresas_criticas.append(e)
            except (AttributeError, TypeError, ValueError):
                continue
        
        context = {
            'page_obj': page_obj,
            'empresas': page_obj,
            'pais_filter': pais_filter,
            'status_filter': status_filter,
            'dias_filter': dias_filter,
            'search_query': search_query,
            'paises': COUNTRY_SETTINGS,
            'stats_por_pais': stats_por_pais,
            'total_empresas': total_empresas,
            'empresas_activas': empresas_activas,
            'empresas_vencidas': empresas_vencidas,
            'empresas_criticas': empresas_criticas,
        }
        
        return render(request, 'admin/suscriptores/lista_suscriptores.html', context)
    except Exception as e:
        logger.error(f"Error en admin_suscriptores: {e}", exc_info=True)
        from django.http import HttpResponse
        error_message = f'Error al cargar el panel de suscriptores: {str(e)}. Por favor, contacta al administrador.'
        return HttpResponse(
            f'<html><body><h1>Error 400 - Bad Request</h1><p>{error_message}</p></body></html>',
            status=400,
            content_type='text/html'
        )


@staff_member_required
@require_http_methods(["POST"])
def extender_suscripcion_ajax(request, empresa_id):
    """
    Vista AJAX para extender suscripción de una empresa
    
    ✅ USA: Empresa.admin_grant_courtesy_extension() que incluye:
    - Auditoría automática
    - Notificaciones automáticas (email + WhatsApp)
    - Validación de duraciones (1, 6, 12 meses)
    - Registro de logs
    
    Parámetros POST:
    - meses: Número de meses a extender (1, 6, 12) - NOTA: Solo acepta 1, 6 o 12
    - enviar_notificacion: 'true' o 'false' (opcional, default: true)
    """
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    try:
        meses = int(request.POST.get('meses', 1))
        enviar_notificacion = request.POST.get('enviar_notificacion', 'true').lower() == 'true'
        
        # ✅ Validar duraciones permitidas (1, 6, 12 meses según admin_grant_courtesy_extension)
        if meses not in [1, 6, 12]:
            return JsonResponse({
                'success': False,
                'error': 'Meses inválidos. Debe ser 1, 6 o 12 meses (según admin_grant_courtesy_extension).'
            }, status=400)
        
        # ✅ USAR admin_grant_courtesy_extension que incluye:
        # - Extensión de fecha
        # - Actualización de estado
        # - Auditoría automática
        # - Notificaciones automáticas (si está configurado)
        resultado = Empresa.admin_grant_courtesy_extension(
            user_email=empresa.user.email,
            duration_months=meses,
            reason=f"Cortesía eGarage - Extendido por {request.user.username}",
            admin_user=request.user
        )
        
        # ✅ admin_grant_courtesy_extension() ya envía notificaciones automáticamente
        # a través de notificar_renovacion_exitosa() con is_courtesy=True
        # NO es necesario enviar notificaciones manualmente
        nueva_fecha_fin = resultado.get('nueva_fecha_fin')
        
        if not nueva_fecha_fin:
            return JsonResponse({
                'success': False,
                'error': 'No se pudo obtener la nueva fecha de expiración del resultado'
            }, status=500)
        
        empresa.refresh_from_db()  # Refrescar para obtener datos actualizados
        
        # Actualizar suscripción si existe
        try:
            suscripcion = empresa.user.suscripcion
            if suscripcion:
                suscripcion.fecha_fin = nueva_fecha_fin.date() if hasattr(nueva_fecha_fin, 'date') else nueva_fecha_fin
                suscripcion.activa = True
                suscripcion.save()
        except Suscripcion.DoesNotExist:
            pass
        except Exception as e:
            # No fallar si hay un error actualizando la suscripción, solo loguear
            logger.warning(f"Error actualizando suscripción después de extender: {e}")
        
        # Formatear fecha para la respuesta
        fecha_fin_str = nueva_fecha_fin.strftime('%Y-%m-%d') if hasattr(nueva_fecha_fin, 'strftime') else str(nueva_fecha_fin)
        
        return JsonResponse({
            'success': True,
            'message': f'✅ Extensión de cortesía otorgada exitosamente por {meses} mes(es). Notificaciones enviadas automáticamente.',
            'nueva_fecha_fin': fecha_fin_str,
            'dias_restantes': empresa.dias_restantes,
            'notificaciones_enviadas': True,  # admin_grant_courtesy_extension siempre envía notificaciones
            'empresa': resultado.get('empresa', empresa.nombre_taller),
        })
        
    except ValueError as e:
        # admin_grant_courtesy_extension lanza ValueError para errores de validación
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        logger.error(f"Error extendiendo suscripción: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error al extender suscripción: {str(e)}'
        }, status=500)


@staff_member_required
def detalle_suscriptor(request, empresa_id):
    """
    Vista de detalle de un suscriptor específico
    """
    empresa = get_object_or_404(Empresa.objects.select_related('user', 'user__suscripcion'), id=empresa_id)
    
    # Obtener suscripción si existe
    try:
        suscripcion = empresa.user.suscripcion
    except Suscripcion.DoesNotExist:
        suscripcion = None
    
    context = {
        'empresa': empresa,
        'suscripcion': suscripcion,
        'dias_restantes': empresa.dias_restantes,
        'config_pais': COUNTRY_SETTINGS.get(empresa.pais, COUNTRY_SETTINGS['CL']),
    }
    
    return render(request, 'admin/suscriptores/detalle_suscriptor.html', context)


@staff_member_required
@require_http_methods(["POST"])
def actualizar_telefono_ajax(request, empresa_id):
    """
    Vista AJAX para actualizar el teléfono de una empresa
    
    Parámetros POST:
    - telefono: Nuevo número de teléfono
    """
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    try:
        nuevo_telefono = request.POST.get('telefono', '').strip()
        
        # Validar que el teléfono no sea demasiado largo
        if len(nuevo_telefono) > 32:
            return JsonResponse({
                'success': False,
                'error': 'El teléfono no puede tener más de 32 caracteres.'
            }, status=400)
        
        # Actualizar teléfono
        empresa.telefono = nuevo_telefono
        empresa.save()
        
        logger.info(f"Teléfono actualizado para empresa {empresa.id} ({empresa.nombre_taller}): {nuevo_telefono}")
        
        return JsonResponse({
            'success': True,
            'message': '✅ Teléfono actualizado exitosamente.',
            'telefono': empresa.telefono,
        })
        
    except Exception as e:
        logger.error(f"Error actualizando teléfono: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error al actualizar teléfono: {str(e)}'
        }, status=500)

