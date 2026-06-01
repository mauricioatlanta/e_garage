# Búsqueda AJAX de clientes por nombre, apellido, email o teléfono
import json
import logging

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import ProtectedError
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from taller.models.clientes import Cliente
from taller.templatetags.country_url import _country_ns_from_path
from taller.utils.chile_locations import ensure_legacy_chile_locations
from taller.utils.empresa import get_active_empresa, get_user_empresa_safe


def ajax_buscar_clientes(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse([], safe=False)

    # BLINDAJE MULTI-TENANT: SIEMPRE filtrar por empresa
    if not request.user.is_authenticated:
        return JsonResponse([], safe=False)

    empresa = get_active_empresa(request)
    if not empresa:
        return JsonResponse([], safe=False)

    clientes = Cliente.objects.filter(empresa=empresa).filter(
        models.Q(nombre__icontains=q)
        | models.Q(apellido__icontains=q)
        | models.Q(email__icontains=q)
        | models.Q(telefono__icontains=q)
    )[:20]

    data = [
        {
            "id": c.pk,
            "nombre": c.nombre,
            "apellido": c.apellido,
            "email": c.email,
            "telefono": c.telefono,
        }
        for c in clientes
    ]
    return JsonResponse(data, safe=False)


from taller.models.region_ciudad import TallerCiudad, TallerRegion
from taller.models.ubicacion import Ciudad as CiudadUSA
from taller.models.ubicacion import Estado as EstadoUSA

DEFAULT_ESTADO_TIMEZONES = {
    "US": "America/New_York",
    "BR": "America/Sao_Paulo",
    "VE": "America/Caracas",
    "PE": "America/Lima",
    "MX": "America/Mexico_City",
}


# Vista unificada que detecta automáticamente el país del usuario
def obtener_ciudades(request):
    """
    Vista inteligente que devuelve ciudades según el país del usuario:
    - Para usuarios de Chile: ciudades de regiones chilenas
    - Para usuarios de USA: ciudades de estados de USA
    - Para usuarios de Brasil: cidades de estados brasileiros
    - Para usuarios de Venezuela: ciudades de estados venezolanos
    - Para usuarios de Perú: ciudades de departamentos peruanos
    """
    # Detectar país del usuario (OneToOne inversa puede lanzar DoesNotExist)
    pais_usuario = "CL"  # Por defecto Chile
    if hasattr(request, "user") and request.user.is_authenticated:
        from taller.utils.empresa import get_user_empresa_safe

        empresa = get_user_empresa_safe(request.user)
        if empresa and getattr(empresa, "pais", None):
            pais_usuario = empresa.pais

    if pais_usuario in ["US", "BR", "VE", "PE", "MX"]:
        # Usuarios de USA, Brasil, Venezuela, Perú: usar modelo Estado/Ciudad unificado
        estado_id = request.GET.get("estado_id")
        if not estado_id:
            return JsonResponse([], safe=False)

        # Filtrar ciudades por estado
        ciudades = CiudadUSA.objects.filter(estado_id=estado_id, estado__pais=pais_usuario).values(
            "id", "nombre"
        )
        return JsonResponse(list(ciudades), safe=False)
    else:
        # Usuario de Chile: devolver ciudades de regiones chilenas (modelo antiguo)
        region_id = request.GET.get("region_id")
        if not region_id:
            return JsonResponse([], safe=False)
        ciudades_qs = TallerCiudad.objects.filter(region_id=region_id)
        if not ciudades_qs.exists():
            ensure_legacy_chile_locations(force=True)
            ciudades_qs = TallerCiudad.objects.filter(region_id=region_id)
        ciudades = ciudades_qs.values("id", "nombre")
        return JsonResponse(list(ciudades), safe=False)


# Mantener compatibilidad con el endpoint específico de USA
def obtener_ciudades_usa(request):
    """
    Endpoint específico para ciudades de USA (mantener compatibilidad)
    """
    estado_id = request.GET.get("estado_id")
    if not estado_id:
        return JsonResponse([], safe=False)
    ciudades = CiudadUSA.objects.filter(estado_id=estado_id).values("id", "nombre")
    return JsonResponse(list(ciudades), safe=False)


from .views_cbv import (
    ClienteCreateView,
    ClienteDetailView,
    ClienteListView,
    ClienteUpdateView,
)

log = logging.getLogger(__name__)


def lista_clientes(request, *args, **kwargs):
    log.info("FBV shim: lista_clientes")
    return ClienteListView.as_view()(request, *args, **kwargs)


def ver_cliente(request, *args, **kwargs):
    log.info("FBV shim: ver_cliente")
    return ClienteDetailView.as_view()(request, *args, **kwargs)


def crear_cliente(request, *args, **kwargs):
    log.info("FBV shim: crear_cliente")

    from taller.utils.empresa import get_or_create_empresa

    # Asegurar que la empresa existe (la crea si falta)
    get_user_empresa_safe(request.user)
    # La vista CBV obtendrá request.user.empresa automáticamente

    view = ClienteCreateView.as_view()
    return view(request, *args, **kwargs)


def editar_cliente(request, *args, **kwargs):
    log.info("FBV shim: editar_cliente")
    return ClienteUpdateView.as_view()(request, *args, **kwargs)


from django.db.models import Count
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "POST"])
def cliente_delete(request, pk=None, cliente_id=None):
    """Elimina un cliente (confirmación con diseño futurista).

    GET -> muestra confirmación.
    POST -> elimina y redirige.

    Acepta tanto pk como cliente_id para compatibilidad.
    """
    # Determinar el ID del cliente
    client_id = pk or cliente_id
    if not client_id:
        raise Http404("No se proporcionó ID de cliente")

    # BLINDAJE MULTI-TENANT: SIEMPRE filtrar por empresa
    if not request.user.is_authenticated:
        raise PermissionDenied("Usuario no autenticado")

    empresa = get_active_empresa(request)
    if not empresa:
        messages.warning(
            request, "Tu usuario no tiene empresa activa. Crea o asigna una empresa primero."
        )
        return redirect("taller:dashboard")

    cliente = get_object_or_404(Cliente, pk=client_id, empresa=empresa)

    if request.method == "POST":
        try:
            cliente.delete()
            messages.success(request, f"Cliente {cliente.nombre} eliminado exitosamente.")
            path = (request.path or "/").strip()
            country_ns = _country_ns_from_path(path)
            if country_ns == "usa":
                return redirect("usa:clientes:lista_clientes")
            if country_ns in ("us_en", "us_es"):
                # Bajo us_en/us_es las rutas están en us_XX:taller:clientes:...
                return redirect(f"{country_ns}:taller:clientes:lista_clientes")
            return redirect("chile:clientes:lista_clientes")
        except ProtectedError as e:
            # Obtener los objetos protegidos
            protected_objects = e.args[1]
            documentos = [obj for obj in protected_objects if obj.__class__.__name__ == "Documento"]

            # Crear mensaje de error informativo
            if documentos:
                doc_ids = [str(doc.id) for doc in documentos[:5]]  # Mostrar máximo 5 IDs
                mensaje = f"No se puede eliminar el cliente {cliente.nombre} porque tiene {len(documentos)} documento(s) asociado(s)"
                if len(documentos) <= 5:
                    mensaje += f": {', '.join(doc_ids)}"
                else:
                    mensaje += f": {', '.join(doc_ids)} y {len(documentos) - 5} más"
                mensaje += ". Elimine primero los documentos asociados."
            else:
                mensaje = f"No se puede eliminar el cliente {cliente.nombre} porque tiene datos relacionados que lo impiden."

            messages.error(request, mensaje)
            return render(
                request,
                "taller/common/clientes/confirmar_eliminacion.html",
                {"cliente": cliente},
            )
        except Exception as e:
            logging.exception("Error inesperado en cliente_delete")
            messages.error(request, f"Error inesperado al eliminar el cliente: {str(e)}")
            return render(
                request,
                "taller/common/clientes/confirmar_eliminacion.html",
                {"cliente": cliente},
            )

    return render(
        request, "taller/common/clientes/confirmar_eliminacion.html", {"cliente": cliente}
    )


def clientes_stats(request):
    """Return JSON with counts of clients per region."""
    # BLINDAJE MULTI-TENANT: SIEMPRE filtrar por empresa del usuario
    if not request.user.is_authenticated:
        return JsonResponse({"labels": [], "counts": []})

    empresa = get_active_empresa(request)
    if not empresa:
        return JsonResponse({"labels": [], "counts": []})

    # Optional filters: start_date, end_date (YYYY-MM-DD), country
    start = request.GET.get("start_date")
    end = request.GET.get("end_date")
    country = request.GET.get("country")

    qs = Cliente.objects.filter(empresa=empresa)
    if country:
        qs = qs.filter(empresa__pais__iexact=country)
    if start:
        qs = qs.filter(created_at__gte=start)
    if end:
        qs = qs.filter(created_at__lte=end)

    agg = qs.values("region__nombre").annotate(count=Count("id")).order_by("-count")
    labels = [row.get("region__nombre") or "Sin región" for row in agg]
    counts = [row["count"] for row in agg]
    return JsonResponse({"labels": labels, "counts": counts})


from django.views.decorators.http import require_http_methods


@require_http_methods(["POST"])
def agregar_ciudad_usa(request):
    """
    Vista AJAX para agregar una nueva ciudad a un estado de USA
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "User not authenticated"})

    # Verificar que el usuario tiene empresa
    empresa = get_active_empresa(request)
    if not empresa:
        return JsonResponse({"success": False, "error": "User without company"})

    try:
        data = json.loads(request.body)
        nombre_ciudad = data.get("nombre", "").strip()
        estado_id = data.get("estado_id")

        if not nombre_ciudad:
            return JsonResponse({"success": False, "error": "City name is required"})

        if not estado_id:
            return JsonResponse({"success": False, "error": "State is required"})

        # Verificar que el estado existe
        try:
            from taller.models.ubicacion import Estado

            estado = Estado.objects.get(id=estado_id)
        except Estado.DoesNotExist:
            return JsonResponse({"success": False, "error": "State not found"})

        # Verificar si la ciudad ya existe en ese estado
        if CiudadUSA.objects.filter(nombre__iexact=nombre_ciudad, estado=estado).exists():
            return JsonResponse({"success": False, "error": "City already exists in this state"})

        # Crear la nueva ciudad
        nueva_ciudad = CiudadUSA.objects.create(nombre=nombre_ciudad, estado=estado)

        return JsonResponse(
            {
                "success": True,
                "ciudad": {"id": nueva_ciudad.id, "nombre": nueva_ciudad.nombre},
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON data"})
    except Exception as e:
        print(f"[ERROR] Error creating USA city: {e}")
        return JsonResponse({"success": False, "error": "Error creating city"})


@require_http_methods(["POST"])
def agregar_ciudad(request):
    """
    Vista AJAX para agregar una nueva ciudad a una región
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Usuario no autenticado"})

    # Verificar que el usuario tiene empresa
    empresa = get_active_empresa(request)
    if not empresa:
        return JsonResponse({"success": False, "error": "Usuario sin empresa"})

    try:
        data = json.loads(request.body)
        nombre_ciudad = data.get("nombre", "").strip()
        region_id = data.get("region_id")

        if not nombre_ciudad:
            return JsonResponse({"success": False, "error": "Nombre de ciudad requerido"})

        if not region_id:
            return JsonResponse({"success": False, "error": "Región requerida"})

        # Detectar país del usuario para usar el modelo correcto
        pais_usuario = empresa.pais if hasattr(empresa, "pais") else "CL"

        if pais_usuario in ["US", "BR", "VE", "PE", "MX"]:
            from taller.models.ubicacion import Ciudad, Estado

            estado_id = data.get("estado_id") or region_id
            if not estado_id:
                return JsonResponse({"success": False, "error": "Estado requerido"})

            try:
                estado = Estado.objects.get(id=estado_id, pais=pais_usuario)
            except Estado.DoesNotExist:
                return JsonResponse({"success": False, "error": "Estado no encontrado"})

            if CiudadUSA.objects.filter(estado=estado, nombre__iexact=nombre_ciudad).exists():
                return JsonResponse(
                    {"success": False, "error": "La ciudad ya existe en este estado"}
                )

            nueva_ciudad = CiudadUSA.objects.create(estado=estado, nombre=nombre_ciudad)

        elif pais_usuario == "CL":
            from taller.models.region_ciudad import TallerCiudad, TallerRegion

            try:
                region = TallerRegion.objects.get(id=region_id)
            except TallerRegion.DoesNotExist:
                return JsonResponse({"success": False, "error": "Región no encontrada"})

            if TallerCiudad.objects.filter(region=region, nombre__iexact=nombre_ciudad).exists():
                return JsonResponse(
                    {"success": False, "error": "La ciudad ya existe en esta región"}
                )

            nueva_ciudad = TallerCiudad.objects.create(region=region, nombre=nombre_ciudad)

        else:
            return JsonResponse({"success": False, "error": "País no soportado"})

        return JsonResponse(
            {
                "success": True,
                "ciudad": {"id": nueva_ciudad.id, "nombre": nueva_ciudad.nombre},
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Datos JSON inválidos"})
    except Exception as e:
        return JsonResponse({"success": False, "error": f"Error interno: {str(e)}"})


@require_http_methods(["POST"])
def agregar_region(request):
    """Crea dinámicamente una región para Chile."""

    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Usuario no autenticado"}, status=401)

    empresa = get_active_empresa(request)
    if not empresa or getattr(empresa, "pais", "CL") != "CL":
        return JsonResponse({"success": False, "error": "Solo disponible para Chile"}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Datos JSON inválidos"}, status=400)

    nombre_region = (data.get("nombre") or "").strip()
    if not nombre_region:
        return JsonResponse({"success": False, "error": "Nombre de región requerido"}, status=400)

    from taller.models.region_ciudad import TallerRegion

    if TallerRegion.objects.filter(nombre__iexact=nombre_region).exists():
        return JsonResponse({"success": False, "error": "La región ya existe"}, status=400)

    region = TallerRegion.objects.create(nombre=nombre_region)
    return JsonResponse({"success": True, "region": {"id": region.id, "nombre": region.nombre}})


@require_http_methods(["POST"])
def agregar_estado(request):
    """Permite crear estados/provincias para países soportados."""

    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Usuario no autenticado"}, status=401)

    empresa = get_active_empresa(request)
    pais = getattr(empresa, "pais", None) if empresa else None
    if not empresa or not pais:
        return JsonResponse({"success": False, "error": "Empresa sin país configurado"}, status=400)

    if pais not in ["US", "BR", "VE", "PE", "MX", "CO", "EC"]:
        return JsonResponse(
            {"success": False, "error": "El país no admite creación dinámica de estados"},
            status=400,
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Datos JSON inválidos"}, status=400)

    nombre_estado = (data.get("nombre") or "").strip()
    codigo_estado = (data.get("codigo") or "").strip().upper()

    if not nombre_estado:
        return JsonResponse({"success": False, "error": "Nombre del estado requerido"}, status=400)

    if not codigo_estado:
        codigo_estado = "".join(fragmento[:2] for fragmento in nombre_estado.split()).upper()
        if not codigo_estado:
            codigo_estado = nombre_estado[:5].upper()

    from taller.models.ubicacion import Estado

    if Estado.objects.filter(pais=pais, nombre__iexact=nombre_estado).exists():
        return JsonResponse({"success": False, "error": "El estado ya existe"}, status=400)

    if Estado.objects.filter(pais=pais, codigo__iexact=codigo_estado).exists():
        return JsonResponse(
            {"success": False, "error": "El código de estado ya está en uso"}, status=400
        )

    timezone = (
        data.get("timezone")
        or getattr(empresa, "zona_horaria", None)
        or DEFAULT_ESTADO_TIMEZONES.get(pais, "UTC")
    )

    estado = Estado.objects.create(
        nombre=nombre_estado,
        codigo=codigo_estado,
        pais=pais,
        timezone=timezone,
    )

    return JsonResponse(
        {
            "success": True,
            "estado": {
                "id": estado.id,
                "nombre": estado.nombre,
                "codigo": estado.codigo,
            },
        }
    )


from django.views.decorators.http import require_http_methods
