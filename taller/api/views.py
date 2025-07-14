from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from taller.models.tienda import Tienda
import json

def api_status(request):
    return JsonResponse({'status': 'ok'})

@csrf_exempt
@require_POST
def crear_tienda_api(request):
    data = json.loads(request.body)
    nombre = data.get('nombre')
    direccion = data.get('direccion', '')
    telefono = data.get('telefono', '')
    if not nombre:
        return JsonResponse({'error': 'El nombre es obligatorio'}, status=400)
    tienda = Tienda.objects.create(nombre=nombre, direccion=direccion, telefono=telefono)
    return JsonResponse({'id': tienda.id, 'nombre': tienda.nombre})
