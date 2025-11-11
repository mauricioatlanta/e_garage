"""
Vistas AJAX para gestión dinámica de ubicaciones (Estados y Ciudades USA).
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from taller.models.ubicacion import Ciudad as CiudadUSA
from taller.models.ubicacion import Estado as EstadoUSA


@login_required
@require_POST
def ajax_crear_estado_usa(request):
    """
    Crea un nuevo estado de USA dinámicamente.
    Retorna JSON con el nuevo estado creado.
    """
    nombre = request.POST.get("nombre", "").strip()
    codigo = request.POST.get("codigo", "").strip().upper()

    if not nombre or not codigo:
        return JsonResponse(
            {"success": False, "error": "State name and code are required"}, status=400
        )

    # Verificar si ya existe
    if EstadoUSA.objects.filter(codigo=codigo).exists():
        estado = EstadoUSA.objects.get(codigo=codigo)
        return JsonResponse(
            {
                "success": True,
                "estado": {
                    "id": estado.id,
                    "nombre": estado.nombre,
                    "codigo": estado.codigo,
                },
                "message": f"State '{nombre}' already exists",
            }
        )

    # Crear nuevo estado
    try:
        estado = EstadoUSA.objects.create(nombre=nombre, codigo=codigo)
        return JsonResponse(
            {
                "success": True,
                "estado": {
                    "id": estado.id,
                    "nombre": estado.nombre,
                    "codigo": estado.codigo,
                },
                "message": f"State '{nombre}' created successfully",
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_POST
def ajax_crear_ciudad_usa(request):
    """
    Crea una nueva ciudad de USA dinámicamente.
    Retorna JSON con la nueva ciudad creada.
    """
    nombre = request.POST.get("nombre", "").strip()
    estado_id = request.POST.get("estado_id", "").strip()

    if not nombre or not estado_id:
        return JsonResponse(
            {"success": False, "error": "City name and state are required"}, status=400
        )

    try:
        estado = EstadoUSA.objects.get(pk=int(estado_id))
    except (EstadoUSA.DoesNotExist, ValueError):
        return JsonResponse({"success": False, "error": "Invalid state selected"}, status=400)

    # Verificar si ya existe
    if CiudadUSA.objects.filter(nombre=nombre, estado=estado).exists():
        ciudad = CiudadUSA.objects.get(nombre=nombre, estado=estado)
        return JsonResponse(
            {
                "success": True,
                "ciudad": {
                    "id": ciudad.id,
                    "nombre": ciudad.nombre,
                    "estado_id": ciudad.estado.id,
                    "estado_nombre": ciudad.estado.nombre,
                },
                "message": f"City '{nombre}' already exists in {estado.nombre}",
            }
        )

    # Crear nueva ciudad
    try:
        ciudad = CiudadUSA.objects.create(nombre=nombre, estado=estado)
        return JsonResponse(
            {
                "success": True,
                "ciudad": {
                    "id": ciudad.id,
                    "nombre": ciudad.nombre,
                    "estado_id": ciudad.estado.id,
                    "estado_nombre": ciudad.estado.nombre,
                },
                "message": f"City '{nombre}' created successfully",
            }
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
