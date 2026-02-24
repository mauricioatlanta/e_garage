# -*- coding: utf-8 -*-
"""
API unificada de ubicaciones para todos los países

Convenciones:
- GET only (require_GET)
- Respuestas consistentes: {'states': [...]} o {'cities': [...]}
- Soporta todos los países: CL, US, BR, PE, VE, CO, EC, MX

Endpoints:
  /api/locations?country=CL         → estados/departamentos de Chile
  /api/locations?country=US         → estados de USA
  /api/locations?country=US&state=GA → ciudades de Georgia, USA
  /api/locations?country=PE&state=LIM → ciudades de Lima, Perú
"""
from django.http import JsonResponse
from django.views.decorators.http import require_GET

# Importar modelos de taller (los mejorados con soporte multi-país)
from taller.models.ubicacion import Ciudad, Estado


@require_GET
def locations(request):
    """
    API unificada de ubicaciones (estados/ciudades) para todos los países.

    Query params:
      - country: Código de país (CL, US, BR, PE, VE, CO, EC, MX) - REQUERIDO
      - state: Código de estado (opcional) - Si se provee, devuelve ciudades

    Respuestas:
      - Sin state: {'states': [{id, name, code}, ...]}
      - Con state: {'cities': [{id, name}, ...]}

    Ejemplos:
      /api/locations?country=CL        → estados de Chile
      /api/locations?country=US        → estados de USA
      /api/locations?country=BR        → estados de Brasil
      /api/locations?country=PE        → departamentos de Perú
      /api/locations?country=VE        → estados de Venezuela
      /api/locations?country=US&state=GA  → ciudades de Georgia
      /api/locations?country=PE&state=LIM → ciudades de Lima
    """
    country = (request.GET.get("country") or "").upper()
    state_code = (request.GET.get("state") or "").upper()

    # Validar que country esté presente
    if not country:
        return JsonResponse({"error": 'Parameter "country" is required'}, status=400)

    # Caso 1: Solo country → devolver estados/departamentos
    if country and not state_code:
        states = Estado.objects.filter(pais=country).order_by("nombre")

        data = []
        for s in states:
            # Obtener código del estado (puede ser 'codigo' o 'code' dependiendo del modelo)
            code = getattr(s, "codigo", "") or getattr(s, "code", "") or ""
            data.append({"id": s.id, "name": s.nombre, "code": code})

        return JsonResponse({"states": data})

    # Caso 2: country + state → devolver ciudades
    if country and state_code:
        # Buscar el estado por código y país
        states = Estado.objects.filter(pais=country)

        estado_encontrado = None
        for st in states:
            code = getattr(st, "codigo", "") or getattr(st, "code", "") or ""
            if code.upper() == state_code:
                estado_encontrado = st
                break

        # Si no se encuentra el estado, devolver array vacío
        if not estado_encontrado:
            return JsonResponse({"cities": []})

        # Cargar ciudades del estado
        cities = Ciudad.objects.filter(estado=estado_encontrado).order_by("nombre")

        data = []
        for c in cities:
            data.append({"id": c.id, "name": c.nombre})

        return JsonResponse({"cities": data})

    # Caso por defecto: arrays vacíos
    return JsonResponse({"states": [], "cities": []})


@require_GET
def states_by_country(request, country_code=None):
    """
    Endpoint para obtener estados de un país.
    
    Soporta dos formatos:
    - Path param: /api/locations/states/<country_code>/
    - Query param: /api/locations/states/?country=XX

    Ejemplos:
      /api/locations/states/PE/ → departamentos de Perú
      /api/locations/states/?country=CL → estados de Chile
    """
    # Obtener country desde path param o query param
    country = (country_code or request.GET.get("country") or "").upper()
    
    if not country:
        return JsonResponse({"error": 'Parameter "country" is required'}, status=400)

    states = Estado.objects.filter(pais=country).order_by("nombre")

    data = []
    for s in states:
        code = getattr(s, "codigo", "") or getattr(s, "code", "") or ""
        data.append(
            {
                "id": s.id,
                "name": s.nombre,
                "code": code,
                "sales_tax": float(s.sales_tax) if hasattr(s, "sales_tax") else 0.0,
            }
        )

    return JsonResponse({"states": data})


@require_GET
def cities_by_state(request, state_id=None):
    """
    Endpoint para obtener ciudades de un estado.
    
    Soporta dos formatos:
    - Path param: /api/locations/cities/<state_id>/
    - Query param: /api/locations/cities/?state_id=XX

    Ejemplo:
      /api/locations/cities/25/ → ciudades del estado con ID 25
      /api/locations/cities/?state_id=25 → ciudades del estado con ID 25
    """
    # Obtener state_id desde path param o query param
    state_id_value = state_id or request.GET.get("state_id")
    
    if not state_id_value:
        return JsonResponse({"error": 'Parameter "state_id" is required'}, status=400)
    
    try:
        estado = Estado.objects.get(pk=state_id_value)
    except (Estado.DoesNotExist, ValueError, TypeError):
        return JsonResponse({"error": "State not found"}, status=404)

    cities = Ciudad.objects.filter(estado=estado).order_by("nombre")

    data = []
    for c in cities:
        # Incluir zip_code si existe en el modelo
        city_data = {
            "id": c.id,
            "name": c.nombre,
            "population": c.poblacion if hasattr(c, "poblacion") else None,
            "is_capital": c.es_capital if hasattr(c, "es_capital") else False,
        }
        # Agregar zip_code si existe
        if hasattr(c, "zip_code"):
            city_data["zip_code"] = c.zip_code
        data.append(city_data)

    return JsonResponse({"cities": data, "state": estado.nombre, "country": estado.pais})

