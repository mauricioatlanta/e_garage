from django.http import JsonResponse
from taller.models.modelo import Modelo

def obtener_modelos(request):
    marca_id = request.GET.get("marca_id")
    q = request.GET.get("q", "").strip()
    modelos_qs = Modelo.objects.all()
    if marca_id:
        modelos_qs = modelos_qs.filter(marca_id=marca_id)
    if q:
        modelos_qs = modelos_qs.filter(nombre__icontains=q)
    modelos_qs = modelos_qs.order_by('nombre')
    modelos = [{"id": m.id, "nombre": m.nombre} for m in modelos_qs]
    return JsonResponse(modelos, safe=False)
