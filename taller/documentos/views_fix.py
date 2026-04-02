from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def numero_documento_auto(request):
    tipo = request.GET.get('tipo', 'OT')
    # Aquí puedes poner la lógica real, por ahora devolvemos un número de prueba
    return JsonResponse({'number': 'BUSCANDO...', 'status': 'success'})
