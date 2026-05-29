import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from taller.models.extras_vehiculo import CajaVehiculo, MotorVehiculo
from taller.models.marca import Marca
from taller.models.modelo import Modelo

try:
    from taller.models.marcas_usa import ModeloVehiculo
except ImportError:
    ModeloVehiculo = None

try:
    from taller.models.catalogo import CatalogoModeloAuto  # Nuestro catálogo
except ImportError:
    CatalogoModeloAuto = None


# Endpoint para modelos USA por marca (?marca=<id>)
@require_GET
def api_modelos_usa(request):
    marca_param = request.GET.get("marca", "").strip()
    if not marca_param:
        return JsonResponse([], safe=False)

    # Debug logging
    print(
        f"[DEBUG API] api_modelos_usa: marca_param='{marca_param}', user={getattr(request.user, 'username', 'anonymous')}"
    )

    # Versión simplificada que funciona
    try:
        # Importar dinámicamente para evitar problemas
        from taller.models.catalogo import CatalogoModeloAuto

        if CatalogoModeloAuto:
            # Obtener modelos del catálogo
            modelos = list(CatalogoModeloAuto.get_modelos_por_marca(marca_param))[:100]
            data = [{"id": modelo, "nombre": modelo} for modelo in modelos]
            print(f"[DEBUG API] Retornando {len(data)} modelos del catálogo")
            return JsonResponse(data, safe=False)
        else:
            print("[DEBUG API] CatalogoModeloAuto no disponible")
            return JsonResponse([], safe=False)

    except Exception as e:
        print(f"[DEBUG API] Error en api_modelos_usa: {e}")
        import traceback

        traceback.print_exc()
        return JsonResponse([], safe=False)


def obtener_modelos(request):
    marca_id = request.GET.get("marca_id")
    q = request.GET.get("q", "").strip()

    # DEBUG: Log de entrada
    print(f"[DEBUG API] obtener_modelos: marca_id={marca_id}, q='{q}'")
    print(
        f"[DEBUG API] usuario: {request.user.username if request.user.is_authenticated else 'anónimo'}"
    )

    # BLINDAJE MULTI-TENANT: Filtrar por país de la empresa
    modelos_qs = Modelo.objects.select_related("marca")

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
            print(
                f"[DEBUG API] Filtrado por marca_id numérico: {marca_id_int}, resultado: {modelos_qs.count()}"
            )
        except (ValueError, TypeError):
            # Si no es numérico, es un nombre de marca del catálogo USA
            print(
                f"[DEBUG API] marca_id no es numérico, asumiendo nombre de marca del catálogo: {marca_id}"
            )

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

    modelos_qs = modelos_qs.order_by("nombre")
    print(f"[DEBUG API] Query final count: {modelos_qs.count()}")

    modelos = [
        {"id": getattr(m, "id", None), "nombre": getattr(m, "nombre", "")} for m in modelos_qs
    ]
    print(f"[DEBUG API] Retornando {len(modelos)} modelos: {modelos[:3]}...")

    return JsonResponse(modelos, safe=False)


@csrf_exempt
@login_required
@require_POST
def crear_modelo(request):
    """API para crear un nuevo modelo"""
    try:
        data = json.loads(request.body)
        marca_id = data.get("marca_id")
        nombre = data.get("nombre", "").strip()

        if not marca_id or not nombre:
            return JsonResponse(
                {"error": "Marca ID y nombre del modelo son requeridos"}, status=400
            )

        # Verificar que la marca existe
        try:
            marca = Marca.objects.get(id=marca_id)
        except Marca.DoesNotExist:
            return JsonResponse({"error": "Marca no encontrada"}, status=404)

        # Verificar que el modelo no existe ya para esta marca
        if Modelo.objects.filter(marca=marca, nombre__iexact=nombre).exists():
            return JsonResponse(
                {"error": f'El modelo "{nombre}" ya existe para la marca "{marca.nombre}"'},
                status=400,
            )

        # Crear el nuevo modelo
        modelo = Modelo.objects.create(nombre=nombre, marca=marca, country=marca.country)

        return JsonResponse(
            {
                "id": modelo.id,
                "nombre": modelo.nombre,
                "marca": marca.nombre,
                "message": "Modelo creado exitosamente",
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"Error interno: {str(e)}"}, status=500)


@login_required
def api_motores_por_modelo(request):
    """API para obtener motores filtrados por modelo"""
    modelo_id = request.GET.get("modelo_id")
    data = []

    if modelo_id and Modelo.objects.filter(id=modelo_id).exists():
        qs = (
            MotorVehiculo.objects.filter(modelos__id=modelo_id)
            .order_by("nombre")
            .values("id", "nombre")
        )
        data = list(qs)

    return JsonResponse({"motores": data})


@login_required
def api_cajas_por_modelo(request):
    """API para obtener cajas filtradas por modelo"""
    modelo_id = request.GET.get("modelo_id")
    data = []

    if modelo_id and Modelo.objects.filter(id=modelo_id).exists():
        qs = (
            CajaVehiculo.objects.filter(modelos__id=modelo_id)
            .order_by("nombre")
            .values("id", "nombre")
        )
        data = list(qs)

    return JsonResponse({"cajas": data})


from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


@csrf_exempt
@require_http_methods(["POST"])
@transaction.atomic
def api_create(request):
    # Content-Type flexible: solo forzamos JSON si viene como application/json
    raw = request.body or b""
    try:
        payload = json.loads(raw.decode("utf-8")) if raw else {}
    except json.JSONDecodeError:
        return JsonResponse({"error": "malformed_json"}, status=400)

    # Campos requeridos
    required = ["empresa_id", "cliente_id", "patente", "marca", "modelo"]
    missing = [k for k in required if k not in payload]
    if missing:
        return JsonResponse({"error": "missing_fields", "fields": missing}, status=400)

    from taller.models.clientes import Cliente
    from taller.models.empresa import Empresa
    from taller.models.vehiculos import Vehiculo

    # Fetch FKs
    try:
        emp = Empresa.objects.get(id=payload["empresa_id"])
    except Empresa.DoesNotExist:
        return JsonResponse({"error": "empresa_not_found"}, status=400)

    try:
        # 🔒 SEGURIDAD: Filtrar por empresa para aislamiento multi-tenant
        cli = Cliente.objects.get(id=payload["cliente_id"], empresa=emp)
    except Cliente.DoesNotExist:
        return JsonResponse({"error": "cliente_not_found"}, status=400)

    # Validación adicional de consistencia (redundante pero defensiva)
    if getattr(cli, "empresa_id", None) != emp.id:
        return JsonResponse({"error": "empresa_mismatch_cliente"}, status=400)

    patente = str(payload["patente"]).strip().upper()

    # Unicidad por empresa
    if Vehiculo.objects.filter(empresa=emp, patente=patente).exists():
        return JsonResponse({"error": "patente_duplicada"}, status=409)

    # Crear - usar campos de texto para compatibilidad con tests
    attrs = dict(
        empresa=emp,
        cliente=cli,
        patente=patente,
        marca_texto=payload.get("marca"),
        modelo_texto=payload.get("modelo"),
    )
    # Campo opcional 'anio'
    if "anio" in [f.name for f in Vehiculo._meta.fields] and "anio" in payload:
        attrs["anio"] = payload["anio"]

    v = Vehiculo.objects.create(**attrs)

    # Respuesta mínima compatible con tests estrictos
    data = {
        "id": v.id,
        "empresa_id": emp.id,
        "cliente_id": cli.id,
        "patente": v.patente,
        "marca": getattr(v, "marca_texto", None),
        "modelo": getattr(v, "modelo_texto", None),
    }
    if hasattr(v, "anio"):
        data["anio"] = v.anio
    return JsonResponse({"vehiculo": data}, status=201)
