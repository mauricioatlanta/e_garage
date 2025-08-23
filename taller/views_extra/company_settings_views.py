from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.files.base import ContentFile
from django.conf import settings
from taller.models import CompanySettings
from taller.forms.company_settings_forms import CompanySettingsForm, LogoUploadForm
# from taller.context_processors import invalidate_company_cache
import json
import base64


@login_required
def company_settings_view(request):
    """Vista principal para configuración de empresa"""
    
    # Obtener o crear configuración de empresa
    company_settings, created = CompanySettings.objects.get_or_create(
        user=request.user,
        defaults={
            'company_name': 'Mi Taller',
            'primary_color': '#0d6efd',
            'secondary_color': '#6c757d',
        }
    )
    
    if request.method == 'POST':
        form = CompanySettingsForm(request.POST, request.FILES, instance=company_settings)
        
        if form.is_valid():
            # Guardar cambios
            updated_settings = form.save(commit=False)
            updated_settings.user = request.user
            updated_settings.save()
            
            # Invalidar cache
            # invalidate_company_cache(request.user.id)
            
            messages.success(request, '¡Configuración actualizada exitosamente!')
            
            # Si es una petición AJAX, devolver JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Configuración actualizada exitosamente',
                    'company_name': updated_settings.get_company_name(),
                    'logo_url': updated_settings.get_logo_url(),
                    'primary_color': updated_settings.get_primary_color(),
                    'secondary_color': updated_settings.get_secondary_color(),
                })
            
            return redirect('company_settings')
        
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario')
            
            # Si es AJAX, devolver errores
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    
    else:
        form = CompanySettingsForm(instance=company_settings)
    
    context = {
        'form': form,
        'company_settings': company_settings,
        'created': created,
        'page_title': 'Configuración de Empresa',
        'breadcrumbs': [
            {'name': 'Inicio', 'url': '/'},
            {'name': 'Configuración', 'url': '#'},
        ]
    }
    
    return render(request, 'settings/company_settings.html', context)


@login_required
@require_http_methods(["POST"])
def upload_logo_ajax(request):
    """Vista AJAX para subir logo únicamente"""
    
    if 'logo' not in request.FILES:
        return JsonResponse({
            'success': False,
            'error': 'No se encontró archivo de logo'
        })
    
    form = LogoUploadForm(request.POST, request.FILES)
    
    if form.is_valid():
        try:
            # Obtener configuración existente
            company_settings, created = CompanySettings.objects.get_or_create(
                user=request.user,
                defaults={'company_name': 'Mi Taller'}
            )
            
            # Actualizar logo
            company_settings.logo = form.cleaned_data['logo']
            company_settings.save()
            
            # Invalidar cache
            # invalidate_company_cache(request.user.id)
            
            return JsonResponse({
                'success': True,
                'logo_url': company_settings.get_logo_url(),
                'message': 'Logo actualizado exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al guardar logo: {str(e)}'
            })
    
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        })


@login_required
def preview_branding(request):
    """Vista para previsualizar cambios de branding en tiempo real"""
    
    if request.method == 'POST':
        data = json.loads(request.body)
        
        # Validar datos recibidos
        company_name = data.get('company_name', 'Mi Taller')
        primary_color = data.get('primary_color', '#0d6efd')
        secondary_color = data.get('secondary_color', '#6c757d')
        
        # Generar CSS personalizado
        custom_css = f"""
        :root {{
            --bs-primary: {primary_color};
            --bs-secondary: {secondary_color};
            --company-primary: {primary_color};
            --company-secondary: {secondary_color};
        }}
        
        .navbar-brand {{
            color: {primary_color} !important;
        }}
        
        .btn-primary {{
            background-color: {primary_color};
            border-color: {primary_color};
        }}
        
        .btn-primary:hover {{
            background-color: {primary_color}CC;
            border-color: {primary_color}CC;
        }}
        
        .text-primary {{
            color: {primary_color} !important;
        }}
        
        .border-primary {{
            border-color: {primary_color} !important;
        }}
        """
        
        return JsonResponse({
            'success': True,
            'preview_css': custom_css,
            'company_name': company_name
        })
    
    return JsonResponse({'success': False})


@login_required
def reset_branding(request):
    """Vista para resetear branding a valores por defecto"""
    
    if request.method == 'POST':
        try:
            company_settings = get_object_or_404(CompanySettings, user=request.user)
            
            # Resetear a valores por defecto
            company_settings.company_name = 'eGarage'
            company_settings.primary_color = '#0d6efd'
            company_settings.secondary_color = '#6c757d'
            # Para limpiar el logo, usamos delete() en lugar de None
            if company_settings.logo:
                company_settings.logo.delete(save=False)
            company_settings.tagline = ''
            company_settings.save()
            
            # Invalidar cache
            # invalidate_company_cache(request.user.id)
            
            messages.success(request, 'Branding restablecido a valores por defecto')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Branding restablecido correctamente'
                })
            
            return redirect('company_settings')
            
        except Exception as e:
            messages.error(request, f'Error al restablecer branding: {str(e)}')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
            
            return redirect('company_settings')
    
    return redirect('company_settings')


@login_required
def export_branding_config(request):
    """Vista para exportar configuración de branding"""
    
    try:
        company_settings = get_object_or_404(CompanySettings, user=request.user)
        
        config_data = {
            'company_name': company_settings.company_name,
            'tagline': company_settings.tagline,
            'primary_color': company_settings.primary_color,
            'secondary_color': company_settings.secondary_color,
            'address': company_settings.address,
            'phone': company_settings.phone,
            'email': company_settings.email,
            'website': company_settings.website,
            'tax_id': company_settings.tax_id,
            'currency': company_settings.currency,
            'about_text': company_settings.about_text,
        }
        
        return JsonResponse({
            'success': True,
            'config': config_data,
            'filename': f'branding_config_{request.user.username}.json'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def company_settings_api(request):
    """API para obtener configuración de empresa (para uso en JavaScript)"""
    
    try:
        company_settings = CompanySettings.objects.get(user=request.user)
        
        data = {
            'company_name': company_settings.get_company_name(),
            'tagline': company_settings.tagline,
            'logo_url': company_settings.get_logo_url(),
            'primary_color': company_settings.get_primary_color(),
            'secondary_color': company_settings.get_secondary_color(),
            'address': company_settings.address,
            'phone': company_settings.phone,
            'email': company_settings.email,
            'website': company_settings.website,
            'currency': company_settings.currency,
        }
        
        return JsonResponse({
            'success': True,
            'settings': data
        })
        
    except CompanySettings.DoesNotExist:
        return JsonResponse({
            'success': True,
            'settings': {
                'company_name': 'eGarage',
                'logo_url': '/static/images/egarage_default_logo.png',
                'primary_color': '#0d6efd',
                'secondary_color': '#6c757d',
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
