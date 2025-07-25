from taller.models.extras_vehiculo import MotorVehiculo, CajaVehiculo
from django.contrib.auth.decorators import login_required

# Endpoint para búsqueda AJAX de motores por modelo
@login_required
def buscar_motores_api(request):
    # 🔒 FILTRO POR EMPRESA - Los motores no necesitan filtro por empresa (son globales)
    modelo_id = request.GET.get('modelo_id')
    motores = MotorVehiculo.objects.all()
    if modelo_id:
        motores = motores.filter(modelo_id=modelo_id)
    data = [
        {
            'id': m.pk,
            'nombre': m.nombre
        } for m in motores.order_by('nombre')[:100]
    ]
    return JsonResponse(data, safe=False)

# Endpoint para búsqueda AJAX de cajas por modelo
@login_required
def buscar_cajas_api(request):
    # 🔒 FILTRO POR EMPRESA - Las cajas no necesitan filtro por empresa (son globales)
    modelo_id = request.GET.get('modelo_id')
    cajas = CajaVehiculo.objects.all()
    if modelo_id:
        cajas = cajas.filter(modelo_id=modelo_id)
    data = [
        {
            'id': c.pk,
            'nombre': c.nombre
        } for c in cajas.order_by('nombre')[:100]
    ]
    return JsonResponse(data, safe=False)
from taller.models.modelo import Modelo
# Endpoint para búsqueda AJAX de modelos por marca
@login_required
def buscar_modelos_api(request):
    # 🔒 FILTRO POR EMPRESA - Los modelos no necesitan filtro por empresa (son globales)
    marca_id = request.GET.get('marca_id')
    modelos = Modelo.objects.all()
    if marca_id:
        modelos = modelos.filter(marca_id=marca_id)
    data = [
        {
            'id': m.pk,
            'nombre': m.nombre
        } for m in modelos.order_by('nombre')[:100]
    ]
    return JsonResponse(data, safe=False)
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import models
from taller.models.tienda import Tienda
from taller.models.clientes import Cliente
import json

@login_required
def api_status(request):
    return JsonResponse({'status': 'ok', 'user': request.user.username})

@csrf_exempt
@require_POST
@login_required
def crear_tienda_api(request):
    # Obtener empresa del usuario
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    data = json.loads(request.body)
    nombre = data.get('nombre')
    direccion = data.get('direccion', '')
    telefono = data.get('telefono', '')
    if not nombre:
        return JsonResponse({'error': 'El nombre es obligatorio'}, status=400)
    
    # Crear tienda asociada a la empresa del usuario
    tienda = Tienda.objects.create(
        nombre=nombre, 
        direccion=direccion, 
        telefono=telefono,
        empresa=empresa  # 🔒 FILTRO EMPRESA
    )
    return JsonResponse({'id': tienda.pk, 'nombre': tienda.nombre})

# Endpoint para búsqueda AJAX de clientes
@login_required
def buscar_clientes_api(request):
    # 🔒 FILTRO CRÍTICO POR EMPRESA
    try:
        empresa = request.user.empresa
    except AttributeError:
        from taller.models.empresa import Empresa
        empresa, created = Empresa.objects.get_or_create(
            user=request.user,
            defaults={'nombre_taller': f'Taller de {request.user.username}'}
        )
    
    q = request.GET.get('q', '').strip()
    # FILTRAR SOLO CLIENTES DE LA EMPRESA DEL USUARIO
    clientes = Cliente.objects.filter(empresa=empresa)
    if q:
        clientes = clientes.filter(
            models.Q(nombre__icontains=q) |
            models.Q(apellido__icontains=q) |
            models.Q(email__icontains=q)
        )
    data = [
        {
            'id': c.pk,
            'nombre': c.nombre,
            'apellido': c.apellido,
            'email': c.email or ''
        }
        for c in clientes[:20]
    ]
    return JsonResponse(data, safe=False)
