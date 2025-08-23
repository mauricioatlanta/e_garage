from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from taller.models import TallerRegion


@csrf_exempt
def agregar_region(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        nombre = data.get('nombre')
        if not nombre:
            return JsonResponse({'ok': False, 'error': 'Nombre requerido'})
        region, _ = Region.objects.get_or_create(nombre=nombre)
        return JsonResponse({'ok': True, 'region': {'id': region.id, 'nombre': region.nombre}})

@csrf_exempt
def agregar_ciudad(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        nombre = data.get('nombre')
        region_id = data.get('region_id')
        if not nombre or not region_id:
            return JsonResponse({'ok': False, 'error': 'Nombre y región requeridos'})
        region = Region.objects.get(id=region_id)
        ciudad, _ = Ciudad.objects.get_or_create(nombre=nombre, region=region)
        return JsonResponse({'ok': True, 'ciudad': {'id': ciudad.id, 'nombre': ciudad.nombre}})
