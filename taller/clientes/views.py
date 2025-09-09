# Búsqueda AJAX de clientes por nombre, apellido, email o teléfono
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import ProtectedError
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from taller.models.clientes import Cliente


def ajax_buscar_clientes(request):
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse([], safe=False)

    # BLINDAJE MULTI-TENANT: SIEMPRE filtrar por empresa
    if not request.user.is_authenticated:
        return JsonResponse([], safe=False)

    empresa = getattr(request.user, "empresa", None)
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


import logging

from taller.models.region_ciudad import TallerCiudad
from taller.models.ubicacion import Ciudad


# Vista unificada que detecta automáticamente el país del usuario
def obtener_ciudades(request):
    """
    Vista inteligente que devuelve ciudades según el país del usuario:
    - Para usuarios de Chile: ciudades de regiones chilenas
    - Para usuarios de USA: ciudades de estados de USA
    """
    # Detectar país del usuario
    pais_usuario = "CL"  # Por defecto Chile
    if hasattr(request, "user") and request.user.is_authenticated:
        if hasattr(request.user, "empresa") and hasattr(request.user.empresa, "pais"):
            pais_usuario = request.user.empresa.pais

    if pais_usuario == "US":
        # Usuario de USA: devolver ciudades de estados de USA
        estado_id = request.GET.get("estado_id")
        if not estado_id:
            return JsonResponse([], safe=False)
        ciudades = Ciudad.objects.filter(estado_id=estado_id).values("id", "nombre")
        return JsonResponse(list(ciudades), safe=False)
    else:
        # Usuario de Chile: devolver ciudades de regiones chilenas
        region_id = request.GET.get("region_id")
        if not region_id:
            return JsonResponse([], safe=False)
        ciudades = TallerCiudad.objects.filter(region_id=region_id).values(
            "id", "nombre"
        )
        return JsonResponse(list(ciudades), safe=False)


# Mantener compatibilidad con el endpoint específico de USA
def obtener_ciudades_usa(request):
    """
    Endpoint específico para ciudades de USA (mantener compatibilidad)
    """
    estado_id = request.GET.get("estado_id")
    if not estado_id:
        return JsonResponse([], safe=False)
    ciudades = Ciudad.objects.filter(estado_id=estado_id).values("id", "nombre")
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
    # Pasar empresa explícitamente al formulario
    empresa = getattr(request.user, "empresa", None)
    view = ClienteCreateView.as_view()
    if request.method == "POST":
        request.POST = request.POST.copy()
        # No es necesario modificar POST, solo pasar empresa en kwargs
        return view(request, empresa=empresa, *args, **kwargs)
    return view(request, empresa=empresa, *args, **kwargs)


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

    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        raise PermissionDenied("Usuario sin empresa asignada")

    cliente = get_object_or_404(Cliente, pk=client_id, empresa=empresa)

    if request.method == "POST":
        try:
            cliente.delete()
            messages.success(
                request, f"Cliente {cliente.nombre} eliminado exitosamente."
            )
            return redirect("taller:clientes:lista_clientes")
        except ProtectedError as e:
            # Obtener los objetos protegidos
            protected_objects = e.args[1]
            documentos = [
                obj
                for obj in protected_objects
                if obj.__class__.__name__ == "Documento"
            ]

            # Crear mensaje de error informativo
            if documentos:
                doc_ids = [
                    str(doc.id) for doc in documentos[:5]
                ]  # Mostrar máximo 5 IDs
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
                "taller/clientes/confirmar_eliminacion.html",
                {"cliente": cliente},
            )
        except Exception as e:
            messages.error(
                request, f"Error inesperado al eliminar el cliente: {str(e)}"
            )
            return render(
                request,
                "taller/clientes/confirmar_eliminacion.html",
                {"cliente": cliente},
            )

    return render(
        request, "taller/clientes/confirmar_eliminacion.html", {"cliente": cliente}
    )


def clientes_stats(request):
    """Return JSON with counts of clients per region."""
    # BLINDAJE MULTI-TENANT: SIEMPRE filtrar por empresa del usuario
    if not request.user.is_authenticated:
        return JsonResponse({"labels": [], "counts": []})

    empresa = getattr(request.user, "empresa", None)
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


import json

from django.views.decorators.http import require_http_methods


@require_http_methods(["POST"])
def agregar_ciudad(request):
    """
    Vista AJAX para agregar una nueva ciudad a una región
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Usuario no autenticado"})

    # Verificar que el usuario tiene empresa
    empresa = getattr(request.user, "empresa", None)
    if not empresa:
        return JsonResponse({"success": False, "error": "Usuario sin empresa"})

    try:
        data = json.loads(request.body)
        nombre_ciudad = data.get("nombre", "").strip()
        region_id = data.get("region_id")

        if not nombre_ciudad:
            return JsonResponse(
                {"success": False, "error": "Nombre de ciudad requerido"}
            )

        if not region_id:
            return JsonResponse({"success": False, "error": "Región requerida"})

        # Detectar país del usuario para usar el modelo correcto
        pais_usuario = empresa.pais if hasattr(empresa, "pais") else "CL"

        if pais_usuario == "US":
            # Para usuarios de USA: crear ciudad en Estado
            from taller.models.ubicacion import Ciudad, Estado

            try:
                estado = Estado.objects.get(id=region_id)
            except Estado.DoesNotExist:
                return JsonResponse({"success": False, "error": "Estado no encontrado"})

            # Verificar si la ciudad ya existe
            if Ciudad.objects.filter(
                estado=estado, nombre__iexact=nombre_ciudad
            ).exists():
                return JsonResponse(
                    {"success": False, "error": "La ciudad ya existe en este estado"}
                )

            # Crear nueva ciudad
            nueva_ciudad = Ciudad.objects.create(estado=estado, nombre=nombre_ciudad)

        else:
            # Para usuarios de Chile: crear ciudad en TallerRegion
            from taller.models.region_ciudad import TallerCiudad, TallerRegion

            try:
                region = TallerRegion.objects.get(id=region_id)
            except TallerRegion.DoesNotExist:
                return JsonResponse({"success": False, "error": "Región no encontrada"})

            # Verificar si la ciudad ya existe
            if TallerCiudad.objects.filter(
                region=region, nombre__iexact=nombre_ciudad
            ).exists():
                return JsonResponse(
                    {"success": False, "error": "La ciudad ya existe en esta región"}
                )

            # Crear nueva ciudad
            nueva_ciudad = TallerCiudad.objects.create(
                region=region, nombre=nombre_ciudad
            )

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
