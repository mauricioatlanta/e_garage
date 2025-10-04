from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from taller.models.marca import Marca
from django.core.exceptions import ObjectDoesNotExist

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def _scope(request):
    """Obtiene empresa y país desde el usuario; fallback CL."""
    empresa = getattr(request.user, "empresa", None)
    pais = (getattr(empresa, "pais", None) or "CL").strip().upper()
    return empresa, pais

def _bad_request(msg):
    return JsonResponse({"success": False, "error": msg}, status=400)

def _ok(payload):
    return JsonResponse({"success": True, **payload})

def _to_option(obj):
    """Serializa opcionalmente un objeto con pk y nombre, id siempre str."""
    return {"id": str(obj.pk), "nombre": getattr(obj, "nombre", str(obj))}

def _parse_int(value, name="id"):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Parámetro '{name}' inválido")

# -------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------

@login_required
@require_http_methods(["GET"])
def ajax_marcas(request):
    """Lista de marcas por país (y empresa si aplica)."""
    try:
        empresa, pais = _scope(request)
        qs = Marca.objects.filter(country=pais)
        # Si tu modelo Marca tiene FK empresa, descomenta:
        # if hasattr(Marca, "empresa") and empresa:
        #     qs = qs.filter(empresa=empresa)

        marcas = [_to_option(m) for m in qs.order_by("nombre")]
        return _ok({"marcas": marcas})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def ajax_modelos(request):
    """Modelos por marca (y opcionalmente por año)."""
    try:
        marca_id = request.GET.get("marca_id")
        if not marca_id:
            return _bad_request("Falta parámetro 'marca_id'")

        marca_id = _parse_int(marca_id, "marca_id")

        from taller.models.modelo import Modelo

        empresa, pais = _scope(request)

        # Verifica que la marca exista y sea del país/empresa
        try:
            marca = Marca.objects.get(pk=marca_id, country=pais)
            # Si Marca tiene empresa:
            # if hasattr(Marca, "empresa") and empresa and marca.empresa_id != empresa.id:
            #     return _bad_request("La marca no pertenece a tu empresa")
        except ObjectDoesNotExist:
            return _bad_request("Marca no encontrada en tu país")

        qs = Modelo.objects.filter(marca_id=marca.pk, country=pais)

        # Si Modelo tiene empresa:
        # if hasattr(Modelo, "empresa") and empresa:
        #     qs = qs.filter(empresa=empresa)

        # Filtrado opcional por año si lo ocupas en el frontend:
        anio = request.GET.get("anio")
        if anio:
            try:
                anio_int = _parse_int(anio, "anio")
                if hasattr(Modelo, "anio"):  # solo si existe ese campo
                    qs = qs.filter(anio=anio_int)
            except ValueError:
                return _bad_request("Parámetro 'anio' inválido")

        modelos = [_to_option(m) for m in qs.order_by("nombre")]
        return _ok({"modelos": modelos})

    except ValueError as ve:
        return _bad_request(str(ve))
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def ajax_motores(request):
    """Motores por modelo."""
    try:
        modelo_id = request.GET.get("modelo_id")
        if not modelo_id:
            return _ok({"motores": []})

        modelo_id = _parse_int(modelo_id, "modelo_id")

        from taller.models.extras_vehiculo import MotorVehiculo
        from taller.models.modelo import Modelo

        empresa, pais = _scope(request)

        try:
            modelo = Modelo.objects.select_related("marca").get(pk=modelo_id, country=pais)
            # Si Modelo tiene empresa:
            # if hasattr(Modelo, "empresa") and empresa and modelo.empresa_id != empresa.id:
            #     return _bad_request("El modelo no pertenece a tu empresa")
        except ObjectDoesNotExist:
            return _ok({"motores": []})

        qs = MotorVehiculo.objects.filter(modelos=modelo).order_by("nombre")

        # Si MotorVehiculo tiene empresa/country:
        # if hasattr(MotorVehiculo, "country"):
        #     qs = qs.filter(country=pais)
        # if hasattr(MotorVehiculo, "empresa") and empresa:
        #     qs = qs.filter(empresa=empresa)

        motores = [_to_option(m) for m in qs]
        return _ok({"motores": motores})

    except ValueError as ve:
        return _bad_request(str(ve))
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def ajax_cajas(request):
    """Cajas por modelo."""
    try:
        modelo_id = request.GET.get("modelo_id")
        if not modelo_id:
            return _ok({"cajas": []})

        modelo_id = _parse_int(modelo_id, "modelo_id")

        from taller.models.extras_vehiculo import CajaVehiculo
        from taller.models.modelo import Modelo

        empresa, pais = _scope(request)

        try:
            modelo = Modelo.objects.select_related("marca").get(pk=modelo_id, country=pais)
            # if hasattr(Modelo, "empresa") and empresa and modelo.empresa_id != empresa.id:
            #     return _bad_request("El modelo no pertenece a tu empresa")
        except ObjectDoesNotExist:
            return _ok({"cajas": []})

        qs = CajaVehiculo.objects.filter(modelos=modelo).order_by("nombre")

        # if hasattr(CajaVehiculo, "country"):
        #     qs = qs.filter(country=pais)
        # if hasattr(CajaVehiculo, "empresa") and empresa:
        #     qs = qs.filter(empresa=empresa)

        cajas = [_to_option(c) for c in qs]
        return _ok({"cajas": cajas})

    except ValueError as ve:
        return _bad_request(str(ve))
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@login_required
@require_http_methods(["GET"])
def ajax_motores_cajas(request):
    """Motores y cajas por modelo en una sola respuesta."""
    try:
        modelo_id = request.GET.get("modelo_id")
        if not modelo_id:
            return _ok({"motores": [], "cajas": []})

        modelo_id = _parse_int(modelo_id, "modelo_id")

        from taller.models.extras_vehiculo import CajaVehiculo, MotorVehiculo
        from taller.models.modelo import Modelo

        empresa, pais = _scope(request)

        try:
            modelo = Modelo.objects.select_related("marca").get(pk=modelo_id, country=pais)
            # if hasattr(Modelo, "empresa") and empresa and modelo.empresa_id != empresa.id:
            #     return _bad_request("El modelo no pertenece a tu empresa")
        except ObjectDoesNotExist:
            return _ok({"motores": [], "cajas": [], "error": "Modelo no encontrado"})

        motores_qs = MotorVehiculo.objects.filter(modelos=modelo).order_by("nombre")
        cajas_qs = CajaVehiculo.objects.filter(modelos=modelo).order_by("nombre")

        motores = [_to_option(m) for m in motores_qs]
        cajas = [_to_option(c) for c in cajas_qs]

        return _ok({
            "motores": motores,
            "cajas": cajas,
            "modelo": getattr(modelo, "nombre", str(modelo)),
            "marca": getattr(modelo.marca, "nombre", "N/A") if getattr(modelo, "marca", None) else "N/A",
        })

    except ValueError as ve:
        return _bad_request(str(ve))
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

# -------------------------------------------------------------------
# Endpoints de compatibilidad (decorados también)
# -------------------------------------------------------------------
@login_required
@require_http_methods(["GET"])
def load_modelos(request):
    return ajax_modelos(request)

@login_required
@require_http_methods(["GET"])
def load_marcas(request):
    return ajax_marcas(request)

@login_required
@require_http_methods(["GET"])
def load_motores(request):
    return ajax_motores(request)

@login_required
@require_http_methods(["GET"])
def load_cajas(request):
    return ajax_cajas(request)

@login_required
@require_http_methods(["GET"])
def load_motores_cajas(request):
    return ajax_motores_cajas(request)
