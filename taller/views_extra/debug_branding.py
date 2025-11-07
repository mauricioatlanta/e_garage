from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from taller.models import ConfiguracionEmpresa
from taller.models.empresa import Empresa


@login_required
def debug_branding(request):
    """Vista de diagnóstico temporal para detectar problemas de branding"""
    try:
        # Obtener empresa del usuario
        empresa = None
        config = None
        
        # Buscar empresa del usuario
        try:
            empresa = Empresa.objects.get(user=request.user)
        except Empresa.DoesNotExist:
            try:
                empresa = Empresa.objects.filter(usuario=request.user).first()
            except:
                pass
        
        if empresa:
            try:
                config = ConfiguracionEmpresa.objects.select_related('empresa').get(empresa=empresa)
            except ConfiguracionEmpresa.DoesNotExist:
                config = None
        
        # Si es una petición AJAX, retornar JSON
        if request.headers.get('Accept') == 'application/json':
            response_data = {
                "MEDIA_URL": settings.MEDIA_URL,
                "MEDIA_ROOT": str(settings.MEDIA_ROOT),
                "MEDIA_ROOT_exists": True,
                "user_id": request.user.id,
                "username": request.user.username,
                "empresa_id": empresa.id if empresa else None,
                "empresa_nombre": empresa.nombre_taller if empresa else None,
                "config_exists": config is not None,
                "logo_name": str(config.logo) if config and config.logo else None,
                "logo_url": config.logo.url if config and config.logo else None,
                "nombre_publico": getattr(config, "nombre_publico", None) if config else None,
                "brand_color": getattr(config, "brand_color", None) if config else None,
            }
            
            # Verificar archivos físicos
            if config and config.logo:
                try:
                    response_data["logo_exists"] = config.logo.storage.exists(config.logo.name)
                    response_data["logo_size"] = config.logo.size
                    response_data["logo_path"] = config.logo.path
                except Exception as e:
                    response_data["logo_error"] = str(e)
            
            return JsonResponse(response_data)
        
        # Renderizar template HTML
        context = {
            'empresa': empresa,
            'config': config,
        }
        return render(request, 'debug/branding.html', context)
        
    except Exception as e:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                "error": str(e),
                "MEDIA_URL": getattr(settings, 'MEDIA_URL', 'NOT_SET'),
                "MEDIA_ROOT": str(getattr(settings, 'MEDIA_ROOT', 'NOT_SET')),
            })
        else:
            context = {'error': str(e)}
            return render(request, 'debug/branding.html', context)
