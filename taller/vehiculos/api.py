from django.http import JsonResponse
from django.views.decorators.http import require_GET

try:
    from taller.models.marcas_usa import ModeloVehiculo
    from taller.models.catalogo import CatalogoModeloAuto  # Nuestro catálogo
except ImportError:
    ModeloVehiculo = CatalogoModeloAuto = None

# Endpoint para modelos USA por marca (?marca=<id>)
@require_GET
def api_modelos_usa(request):
    marca_param = request.GET.get('marca', '').strip()
    if not marca_param:
        return JsonResponse([], safe=False)
    
    # Usar nuestro catálogo importado
    if CatalogoModeloAuto:
        # El parámetro marca viene como nombre de marca, no ID
        modelos = CatalogoModeloAuto.get_modelos_por_marca(marca_param)[:100]
        # CORREGIDO: get_modelos_por_marca retorna strings directamente, no diccionarios
        data = [{'id': modelo, 'nombre': modelo} for modelo in modelos]
        return JsonResponse(data, safe=False)
    
    # Fallback al modelo antiguo si existe
    elif ModeloVehiculo:
        try:
            marca_id = int(marca_param)
            qs = ModeloVehiculo.objects.filter(marca_id=marca_id, activo=True).order_by('nombre')
            data = [{'id': getattr(m, 'id', None), 'nombre': getattr(m, 'nombre', '')} for m in qs]
            return JsonResponse(data, safe=False)
        except (ValueError, TypeError):
            return JsonResponse([], safe=False)
    
    return JsonResponse([], safe=False)
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
    modelos = [{"id": getattr(m, 'id', None), "nombre": getattr(m, 'nombre', '')} for m in modelos_qs]
    return JsonResponse(modelos, safe=False)
