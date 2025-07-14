from django.http import JsonResponse
from taller.models.modelo import Modelo

def obtener_modelos(request):
    marca_id = request.GET.get("marca_id")
    modelos = []
    if marca_id:
        modelos_qs = Modelo.objects.filter(marca_id=marca_id).order_by('nombre')
        modelos = [{"id": m.id, "nombre": m.nombre} for m in modelos_qs]
    return JsonResponse(modelos, safe=False)
