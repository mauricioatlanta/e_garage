from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from taller.models.modelo import Modelo
from taller.models.marca import Marca
from taller.models.extras_vehiculo import MotorVehiculo, CajaVehiculo

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
    
    # DEBUG: Log de entrada
    print(f"[DEBUG API] obtener_modelos: marca_id={marca_id}, q='{q}'")
    print(f"[DEBUG API] usuario: {request.user.username if request.user.is_authenticated else 'anónimo'}")
    
    # BLINDAJE MULTI-TENANT: Filtrar por país de la empresa
    modelos_qs = Modelo.objects.select_related('marca')
    
    # TEMPORAL: Comentar filtrado por país para debug
    # user = request.user
    # if hasattr(user, 'empresa') and user.empresa and hasattr(user.empresa, 'pais'):
    #     pais = user.empresa.pais
    #     print(f"[DEBUG API] Filtrando por país: {pais}")
    #     modelos_qs = modelos_qs.filter(country=pais)
    # else:
    #     print(f"[DEBUG API] Usuario sin empresa o empresa sin país. User empresa: {getattr(user, 'empresa', None)}")
    
    print(f"[DEBUG API] Total modelos sin filtro país: {modelos_qs.count()}")
    
    if marca_id:
        # IMPORTANTE: Para usuarios de USA, marca_id puede ser un nombre de marca del catálogo
        # Para usuarios de Chile, marca_id es un ID numérico
        try:
            # Intentar convertir a entero (caso Chile)
            marca_id_int = int(marca_id)
            modelos_qs = modelos_qs.filter(marca_id=marca_id_int)
            print(f"[DEBUG API] Filtrado por marca_id numérico: {marca_id_int}, resultado: {modelos_qs.count()}")
        except (ValueError, TypeError):
            # Si no es numérico, es un nombre de marca del catálogo USA
            print(f"[DEBUG API] marca_id no es numérico, asumiendo nombre de marca del catálogo: {marca_id}")
            
            # Para usuarios de USA, usar el catálogo
            try:
                from taller.models.catalogo import CatalogoModeloAuto
                if CatalogoModeloAuto:
                    modelos = CatalogoModeloAuto.get_modelos_por_marca(marca_id)
                    # Convertir a formato compatible con la API
                    modelos_data = [{"id": modelo, "nombre": modelo} for modelo in modelos]
                    print(f"[DEBUG API] Retornando {len(modelos_data)} modelos del catálogo USA")
                    return JsonResponse(modelos_data, safe=False)
            except ImportError:
                print("[DEBUG API] No se puede importar CatalogoModeloAuto")
                pass
            
            # Si no se puede usar el catálogo, retornar lista vacía
            print("[DEBUG API] No se pudo obtener modelos del catálogo, retornando lista vacía")
            return JsonResponse([], safe=False)
    
    if q:
        modelos_qs = modelos_qs.filter(nombre__icontains=q)
        print(f"[DEBUG API] Filtrado por query: {q}")
    
    modelos_qs = modelos_qs.order_by('nombre')
    print(f"[DEBUG API] Query final count: {modelos_qs.count()}")
    
    modelos = [{"id": getattr(m, 'id', None), "nombre": getattr(m, 'nombre', '')} for m in modelos_qs]
    print(f"[DEBUG API] Retornando {len(modelos)} modelos: {modelos[:3]}...")
    
    return JsonResponse(modelos, safe=False)

@csrf_exempt
@login_required
@require_POST
def crear_modelo(request):
    """API para crear un nuevo modelo"""
    try:
        data = json.loads(request.body)
        marca_id = data.get('marca_id')
        nombre = data.get('nombre', '').strip()
        
        if not marca_id or not nombre:
            return JsonResponse({
                'error': 'Marca ID y nombre del modelo son requeridos'
            }, status=400)
        
        # Verificar que la marca existe
        try:
            marca = Marca.objects.get(id=marca_id)
        except Marca.DoesNotExist:
            return JsonResponse({
                'error': 'Marca no encontrada'
            }, status=404)
        
        # Verificar que el modelo no existe ya para esta marca
        if Modelo.objects.filter(marca=marca, nombre__iexact=nombre).exists():
            return JsonResponse({
                'error': f'El modelo "{nombre}" ya existe para la marca "{marca.nombre}"'
            }, status=400)
        
        # Crear el nuevo modelo
        modelo = Modelo.objects.create(
            nombre=nombre,
            marca=marca,
            country=marca.country
        )
        
        return JsonResponse({
            'id': modelo.id,
            'nombre': modelo.nombre,
            'marca': marca.nombre,
            'message': 'Modelo creado exitosamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'JSON inválido'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Error interno: {str(e)}'
        }, status=500)


@login_required
def api_motores_por_modelo(request):
    """API para obtener motores filtrados por modelo"""
    modelo_id = request.GET.get('modelo_id')
    data = []
    
    if modelo_id and Modelo.objects.filter(id=modelo_id).exists():
        qs = MotorVehiculo.objects.filter(modelos__id=modelo_id).order_by('nombre').values('id', 'nombre')
        data = list(qs)
    
    return JsonResponse(data, safe=False)


@login_required
def api_cajas_por_modelo(request):
    """API para obtener cajas filtradas por modelo"""
    modelo_id = request.GET.get('modelo_id')
    data = []
    
    if modelo_id and Modelo.objects.filter(id=modelo_id).exists():
        qs = CajaVehiculo.objects.filter(modelos__id=modelo_id).order_by('nombre').values('id', 'nombre')
        data = list(qs)
    
    return JsonResponse(data, safe=False)
