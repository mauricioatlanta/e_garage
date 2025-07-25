from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json

@login_required
def configurar_timezone(request):
    """
    Vista para configurar la zona horaria del taller
    """
    empresa = request.user.empresa
    
    if request.method == 'POST':
        nueva_zona = request.POST.get('zona_horaria')
        
        # Validar que la zona horaria es válida
        zonas_validas = [choice[0] for choice in empresa.TIMEZONE_CHOICES]
        
        if nueva_zona in zonas_validas:
            empresa.zona_horaria = nueva_zona
            empresa.save()
            
            messages.success(request, f'Zona horaria actualizada a {empresa.timezone_display}')
            return redirect('configurar_timezone')
        else:
            messages.error(request, 'Zona horaria no válida')
    
    context = {
        'empresa': empresa,
        'timezone_choices': empresa.TIMEZONE_CHOICES,
        'current_timezone': empresa.zona_horaria,
        'current_time': empresa.now_local(),
        'formatted_time': empresa.format_local_datetime(empresa.now_local(), 'full')
    }
    
    return render(request, 'taller/configuracion/timezone.html', context)

@login_required
@require_http_methods(["POST"])
def cambiar_timezone_ajax(request):
    """
    API para cambiar zona horaria vía AJAX
    """
    try:
        data = json.loads(request.body)
        nueva_zona = data.get('zona_horaria')
        
        empresa = request.user.empresa
        zonas_validas = [choice[0] for choice in empresa.TIMEZONE_CHOICES]
        
        if nueva_zona in zonas_validas:
            empresa.zona_horaria = nueva_zona
            empresa.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Zona horaria actualizada a {empresa.timezone_display}',
                'new_timezone': empresa.timezone_display,
                'current_time': empresa.format_local_datetime(empresa.now_local(), 'full')
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Zona horaria no válida'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def preview_timezone(request):
    """
    API para previsualizar cómo se vería una zona horaria
    """
    zona_horaria = request.GET.get('timezone')
    
    if not zona_horaria:
        return JsonResponse({'error': 'No timezone provided'})
    
    try:
        import pytz
        from django.utils import timezone
        
        # Crear un objeto temporal para previsualizar
        tz = pytz.timezone(zona_horaria)
        now_utc = timezone.now()
        now_local = now_utc.astimezone(tz)
        
        # Encontrar el nombre legible
        timezone_choices = dict(request.user.empresa.TIMEZONE_CHOICES)
        display_name = timezone_choices.get(zona_horaria, zona_horaria)
        
        return JsonResponse({
            'success': True,
            'timezone_display': display_name,
            'current_time': now_local.strftime("%m/%d/%Y – %I:%M %p"),
            'preview': f'La hora actual en {display_name} sería: {now_local.strftime("%I:%M %p")}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error al previsualizar timezone: {str(e)}'
        })
