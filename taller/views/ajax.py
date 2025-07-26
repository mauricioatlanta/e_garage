from django.http import JsonResponse
from utils import pais

def ciudades_por_region(request):
    pais_codigo = request.GET.get('pais')
    region = request.GET.get('region')
    ciudades = pais.get_ciudades(pais_codigo, region)
    return JsonResponse({'ciudades': ciudades})
