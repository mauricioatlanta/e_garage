from django.http import JsonResponse
from taller.models.clientes import Cliente

def info_cliente(request):
    cliente_id = request.GET.get('id')
    try:
        cliente = Cliente.objects.get(pk=cliente_id)
        return JsonResponse({
            'nombre': cliente.nombre,
            'apellido': cliente.apellido,
            'telefono': cliente.telefono,
            'email': cliente.email,
            'ciudad': str(cliente.ciudad) if cliente.ciudad else '',
        })
    except Cliente.DoesNotExist:
        return JsonResponse({}, status=404)