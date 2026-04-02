from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

@csrf_exempt
@require_GET
def buscar_clientes_public(request):
    try:
        termino = (request.GET.get("q") or "").strip()
        
        if len(termino) < 2:
            return JsonResponse({'success': True, 'results': []})
        
        from taller.models import Cliente
        from django.db.models import Q
        
        # Búsqueda sin usar rut (usa los campos que existen)
        clientes = Cliente.objects.filter(
            Q(nombre__icontains=termino) | 
            Q(apellido__icontains=termino) |
            Q(email__icontains=termino) |
            Q(telefono__icontains=termino)
        )[:20]
        
        resultados = []
        for c in clientes:
            nombre = f"{c.nombre} {c.apellido}".strip() if hasattr(c, 'apellido') else c.nombre
            resultados.append({
                'id': c.id,
                'nombre': nombre,
                'telefono': getattr(c, 'telefono', ''),
                'email': getattr(c, 'email', ''),
                'texto': nombre
            })
        
        return JsonResponse({'success': True, 'results': resultados})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=200)
