from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from taller.models.perfil_usuario import PerfilUsuario
from taller.models.mecanico import Mecanico
from taller.models.empresa import Empresa
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import re
import os

@login_required
def configuracion_empresa(request):
    """
    Vista principal de configuración del taller
    """
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        empresa = perfil.empresa
    except PerfilUsuario.DoesNotExist:
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={
                'nombre_taller': f'Taller de {request.user.username}',
                'telefono': '',
                'email': request.user.email or '',
                'direccion': ''
            }
        )
        perfil = PerfilUsuario.objects.create(user=request.user, empresa=empresa)
        messages.info(request, '✅ Se ha creado un perfil básico para tu usuario.')

    if request.method == 'POST':
        if 'actualizar_empresa' in request.POST:
            nombre_taller = request.POST.get('nombre_taller', '').strip()
            empresa_nombre = request.POST.get('empresa_nombre', '').strip()
            telefono = request.POST.get('telefono', '').strip()
            email = request.POST.get('email', '').strip()
            direccion = request.POST.get('direccion', '').strip()
            
            if nombre_taller:
                empresa.nombre_taller = nombre_taller
                empresa.empresa = empresa_nombre
                empresa.telefono = telefono
                empresa.email = email
                empresa.direccion = direccion
                
                # Manejar logo
                if 'logo' in request.FILES:
                    logo_file = request.FILES['logo']
                    if logo_file.size > 5 * 1024 * 1024:  # 5MB máximo
                        messages.error(request, '❌ El logo no puede exceder 5MB.')
                    elif not logo_file.content_type.startswith('image/'):
                        messages.error(request, '❌ El archivo debe ser una imagen.')
                    else:
                        # Eliminar logo anterior si existe
                        if empresa.logo:
                            if default_storage.exists(empresa.logo.name):
                                default_storage.delete(empresa.logo.name)
                        
                        # Asignar nuevo logo
                        empresa.logo = logo_file
                        messages.success(request, '📷 Logo actualizado exitosamente.')
                
                empresa.save()
                messages.success(request, '✅ Información de la empresa actualizada exitosamente.')
            else:
                messages.error(request, '❌ El nombre del taller es obligatorio.')

    # Obtener estadísticas
    mecanicos_total = Mecanico.objects.filter(empresa=empresa).count()
    mecanicos_activos = Mecanico.objects.filter(empresa=empresa, activo=True).count()
    mecanicos_inactivos = mecanicos_total - mecanicos_activos
    
    from taller.models.documento import Documento
    documentos_total = Documento.objects.filter(empresa=empresa).count()
    
    context = {
        'empresa': empresa,
        'stats': {
            'mecanicos_total': mecanicos_total,
            'mecanicos_activos': mecanicos_activos,
            'mecanicos_inactivos': mecanicos_inactivos,
            'documentos_total': documentos_total,
        }
    }
    
    return render(request, 'taller/configuracion/empresa.html', context)
@login_required
def configuracion_mecanicos(request):
    """
    Vista para gestionar los mecánicos del taller
    """
    try:
        perfil = PerfilUsuario.objects.get(user=request.user)
        empresa = perfil.empresa
    except PerfilUsuario.DoesNotExist:
        # Si no tiene perfil, crear empresa y perfil básicos
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={
                'nombre_taller': f'Taller de {request.user.username}',
                'telefono': '',
                'email': request.user.email or '',
                'direccion': ''
            }
        )
        perfil = PerfilUsuario.objects.create(user=request.user, empresa=empresa)
        messages.info(request, '✅ Se ha creado un perfil básico para tu usuario.')

    if request.method == 'POST':
        if 'crear_mecanico' in request.POST:
            nombre = request.POST.get('nombre_nuevo_mecanico', '').strip()
            telefono = request.POST.get('telefono_nuevo_mecanico', '').strip()
            direccion = request.POST.get('direccion_nuevo_mecanico', '').strip()
            
            if nombre:
                # Validar formato de teléfono básico
                if telefono and not re.match(r'^[\d\s\-\+\(\)]+$', telefono):
                    messages.error(request, '❌ Formato de teléfono inválido.')
                elif len(nombre) < 2:
                    messages.error(request, '❌ El nombre debe tener al menos 2 caracteres.')
                elif Mecanico.objects.filter(empresa=empresa, nombre__iexact=nombre).exists():
                    messages.error(request, f'❌ Ya existe un mecánico con el nombre "{nombre}" en tu taller.')
                else:
                    Mecanico.objects.create(
                        empresa=empresa, 
                        nombre=nombre, 
                        telefono=telefono,
                        direccion=direccion,
                        activo=True
                    )
                    messages.success(request, f'✅ Mecánico "{nombre}" agregado exitosamente.')
            else:
                messages.error(request, '❌ Por favor, ingresa un nombre válido.')

        elif 'desactivar_mecanico' in request.POST:
            mecanico_id = request.POST.get('mecanico_id')
            mecanico = Mecanico.objects.filter(id=mecanico_id, empresa=empresa).first()
            if mecanico:
                mecanico.activo = False
                mecanico.save()
                messages.success(request, f'❌ Mecánico "{mecanico.nombre}" desactivado. Ya no aparecerá en formularios nuevos.')

        elif 'activar_mecanico' in request.POST:
            mecanico_id = request.POST.get('mecanico_id')
            mecanico = Mecanico.objects.filter(id=mecanico_id, empresa=empresa).first()
            if mecanico:
                mecanico.activo = True
                mecanico.save()
                messages.success(request, f'✅ Mecánico "{mecanico.nombre}" reactivado.')

        elif 'editar_mecanico' in request.POST:
            mecanico_id = request.POST.get('mecanico_id')
            nuevo_nombre = request.POST.get('nuevo_nombre', '').strip()
            nuevo_telefono = request.POST.get('nuevo_telefono', '').strip()
            nueva_direccion = request.POST.get('nueva_direccion', '').strip()
            mecanico = Mecanico.objects.filter(id=mecanico_id, empresa=empresa).first()
            
            if mecanico and nuevo_nombre and len(nuevo_nombre) >= 2:
                # Validar teléfono si se proporciona
                if nuevo_telefono and not re.match(r'^[\d\s\-\+\(\)]+$', nuevo_telefono):
                    messages.error(request, f'❌ Formato de teléfono inválido.')
                elif Mecanico.objects.filter(empresa=empresa, nombre__iexact=nuevo_nombre).exclude(id=mecanico_id).exists():
                    messages.error(request, f'❌ Ya existe otro mecánico con el nombre "{nuevo_nombre}".')
                else:
                    nombre_anterior = mecanico.nombre
                    mecanico.nombre = nuevo_nombre
                    mecanico.telefono = nuevo_telefono
                    mecanico.direccion = nueva_direccion
                    mecanico.save()
                    messages.success(request, f'✏️ Mecánico "{nombre_anterior}" actualizado exitosamente.')
            elif not nuevo_nombre or len(nuevo_nombre) < 2:
                messages.error(request, '❌ El nombre debe tener al menos 2 caracteres.')

        elif 'eliminar_mecanico' in request.POST:
            mecanico_id = request.POST.get('mecanico_id')
            mecanico = Mecanico.objects.filter(id=mecanico_id, empresa=empresa).first()
            if mecanico:
                # Verificar si el mecánico tiene documentos asociados
                from taller.models.documento import Documento
                documentos_asociados = Documento.objects.filter(mecanico=mecanico).count()
                if documentos_asociados > 0:
                    messages.warning(request, f'⚠️ No se puede eliminar "{mecanico.nombre}" porque tiene {documentos_asociados} documentos asociados. Se ha desactivado en su lugar.')
                    mecanico.activo = False
                    mecanico.save()
                else:
                    nombre = mecanico.nombre
                    mecanico.delete()
                    messages.success(request, f'🗑️ Mecánico "{nombre}" eliminado completamente.')

        return redirect('configuracion_mecanicos')

    # Obtener mecánicos ordenados: primero los activos, luego por nombre
    mecanicos = Mecanico.objects.filter(empresa=empresa).order_by('-activo', 'nombre')
    mecanicos_activos = mecanicos.filter(activo=True).count()
    mecanicos_inactivos = mecanicos.filter(activo=False).count()
    
    return render(request, 'taller/configuracion/mecanicos.html', {
        'mecanicos': mecanicos,
        'empresa': empresa,
        'stats': {
            'total': mecanicos.count(),
            'activos': mecanicos_activos,
            'inactivos': mecanicos_inactivos
        }
    })
