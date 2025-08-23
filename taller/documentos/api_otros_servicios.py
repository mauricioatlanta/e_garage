
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required

# Endpoint para buscar otros servicios por nombre (subcategoría especiales/emergencias)
@login_required
@require_GET
def api_buscar_otros_servicios(request):
    """
    API para buscar otros servicios por nombre (solo subcategoría especiales/emergencias)
    """
    query = request.GET.get('q', '').strip()
    country = request.GET.get('country', 'CL')
    subcat_code = request.GET.get('subcat_code', 'especiales')
    if len(query) < 2:
        return JsonResponse({'servicios': []})
    subcat = SubcategoriaServicio.objects.filter(code=subcat_code, country=country).first()
    if not subcat:
        return JsonResponse({'servicios': []})
    servicios = Servicio.objects.filter(
        subcategoria=subcat,
        country=country,
        names__label__icontains=query
    ).distinct()[:20]
    servicios_data = []
    for servicio in servicios:
        nombre = servicio.get_label('es')
        servicios_data.append({
            'id': servicio.pk,
            'nombre': nombre,
            'subcategoria': subcat.get_label('es')
        })
    return JsonResponse({'servicios': servicios_data})
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from taller.servicios.models import CategoriaServicio, SubcategoriaServicio, Servicio, ServicioName
import json

@login_required
@require_POST
def api_crear_otro_servicio_rapido(request):
    """
    API para crear un 'otro servicio' rápido cuando no existe en la lista
    """
    data = json.loads(request.body)
    nombre_es = data.get('nombre_es', '').strip()
    nombre_en = data.get('nombre_en', '').strip()
    country = data.get('country', 'CL')
    subcat_code = data.get('subcat_code', 'especiales')  # 'especiales' o 'emergencias'

    if not nombre_es:
        return JsonResponse({'error': 'Nombre en español requerido'}, status=400)
    if not nombre_en:
        return JsonResponse({'error': 'Nombre en inglés requerido'}, status=400)

    # Buscar o crear la subcategoría adecuada
    subcat = SubcategoriaServicio.objects.filter(code=subcat_code, country=country).first()
    if not subcat:
        return JsonResponse({'error': 'No existe la subcategoría para otros servicios'}, status=400)

    # Crear el servicio
    servicio, created = Servicio.objects.get_or_create(
        subcategoria=subcat,
        country=country,
        code=nombre_es[:48],
        defaults={'tipo': 'externo'}
    )
    if created:
        ServicioName.objects.create(servicio=servicio, language='es', label=nombre_es, is_default=True)
        ServicioName.objects.create(servicio=servicio, language='en', label=nombre_en, is_default=True)
        return JsonResponse({
            'success': True,
            'servicio': {
                'id': servicio.pk,
                'nombre': nombre_es,
                'subcategoria': subcat.get_label()
            }
        })
    else:
        return JsonResponse({
            'success': True,
            'servicio': {
                'id': servicio.pk,
                'nombre': nombre_es,
                'subcategoria': subcat.get_label()
            },
            'mensaje': 'El otro servicio ya existía'
        })
