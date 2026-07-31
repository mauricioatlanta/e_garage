import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from taller.models.empresa import Empresa
from taller.models.repuesto import Repuesto

from .views_cbv import (
    RepuestoCreateView,
    RepuestoDetailView,
    RepuestoListView,
    RepuestoUpdateView,
)

log = logging.getLogger(__name__)


def lista_repuestos(request, *args, **kwargs):
    log.info("FBV shim: lista_repuestos")
    return RepuestoListView.as_view()(request, *args, **kwargs)


def ver_repuesto(request, *args, **kwargs):
    log.info("FBV shim: ver_repuesto")
    return RepuestoDetailView.as_view()(request, *args, **kwargs)


def crear_repuesto(request, *args, **kwargs):
    log.info("FBV shim: crear_repuesto")
    return RepuestoCreateView.as_view()(request, *args, **kwargs)


def editar_repuesto(request, *args, **kwargs):
    log.info("FBV shim: editar_repuesto")
    return RepuestoUpdateView.as_view()(request, *args, **kwargs)


def eliminar_repuesto(request, pk):
    """Eliminar un repuesto - FILTRADO POR EMPRESA"""
    if request.method == "POST":
        try:
            # 🔒 BLINDAJE MULTI-TENANT: SIEMPRE filtrar por empresa
            empresa = getattr(request.user, "empresa", None)
            if not empresa:
                return JsonResponse(
                    {"success": False, "error": "Usuario sin empresa asignada"}, status=403
                )

            repuesto = get_object_or_404(Repuesto, pk=pk, empresa=empresa)
            repuesto.delete()
            messages.success(request, "Repuesto eliminado exitosamente.")
            return JsonResponse({"success": True})
        except Exception as e:
            log.error(f"Error al eliminar repuesto: {e}")
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    else:
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)


@require_GET
@login_required
def buscar_repuestos_workspace(request, *args, **kwargs):
    """
    Endpoint de búsqueda de repuestos para el Workspace PARTS 2.0.

    Contrato JSON compatible con workspace_search.js:
      GET ?q=<query>
      → { "query": str, "vehiculos": [...repuestos...], "clientes": [], "meta": {...} }

    Prioridad de resultados:
      1. part_number exacto (case-insensitive)
      2. part_number istartswith  /  nombre istartswith
      3. part_number icontains    /  nombre icontains    /  proveedor icontains
    Límite total: 10 resultados.
    """
    from taller.utils.empresa import get_active_empresa, get_or_create_empresa, get_user_empresa_safe
    from taller.views_ingreso import _workspace_prefix_from_request

    q = (request.GET.get("q") or "").strip()
    prefix = _workspace_prefix_from_request(request)

    if len(q) < 2:
        return JsonResponse({
            "query": q,
            "vehiculos": [],
            "clientes": [],
            "meta": {"min_chars": 2, "vehiculos": 0, "clientes": 0, "total": 0},
        })

    empresa = get_active_empresa(request) or get_user_empresa_safe(request.user)
    if not empresa:
        empresa = get_or_create_empresa(request)
    if not empresa:
        return JsonResponse({
            "query": q,
            "vehiculos": [],
            "clientes": [],
            "meta": {"min_chars": 2, "vehiculos": 0, "clientes": 0, "total": 0},
        })

    base_qs = Repuesto.objects.filter(empresa=empresa)

    # Priority 1: exact part_number match
    exact_qs = base_qs.filter(part_number__iexact=q)
    exact_pks = set(exact_qs.values_list("pk", flat=True))

    # Priority 2: starts-with on part_number or nombre
    prefix_qs = base_qs.filter(
        Q(part_number__istartswith=q) | Q(nombre__istartswith=q)
    ).exclude(pk__in=exact_pks)
    prefix_pks = set(exact_pks) | set(prefix_qs.values_list("pk", flat=True))

    # Priority 3: contains on part_number, nombre, proveedor
    fuzzy_qs = base_qs.filter(
        Q(part_number__icontains=q)
        | Q(nombre__icontains=q)
        | Q(proveedor__icontains=q)
    ).exclude(pk__in=prefix_pks)

    # Combine, cap at 10 total
    MAX = 10
    exact_list   = list(exact_qs.order_by("nombre")[:MAX])
    remaining    = MAX - len(exact_list)
    prefix_list  = list(prefix_qs.order_by("nombre")[:remaining]) if remaining > 0 else []
    remaining   -= len(prefix_list)
    fuzzy_list   = list(fuzzy_qs.order_by("nombre")[:remaining]) if remaining > 0 else []

    results = exact_list + prefix_list + fuzzy_list

    def _serialize(r):
        parts = []
        if r.part_number:
            parts.append(f"PN {r.part_number}")
        parts.append(f"Stock {r.cantidad_stock}")
        return {
            "id":       r.id,
            "type":     "repuesto",
            "title":    r.nombre,
            "subtitle": " · ".join(parts),
            "url":      f"{prefix}/repuestos/{r.pk}/",
            "meta":     str(r.precio_venta),
        }

    data = [_serialize(r) for r in results]
    return JsonResponse({
        "query":    q,
        "vehiculos": data,
        "clientes":  [],
        "meta": {
            "min_chars": 2,
            "vehiculos": len(data),
            "clientes":  0,
            "total":     len(data),
        },
    })


@login_required
@login_required
@csrf_exempt
def buscar_repuestos_ajax(request):
    """Búsqueda inteligente en tiempo real de repuestos"""
    try:
        log.info(f"Búsqueda AJAX iniciada - Método: {request.method}")
        log.info(f"Usuario: {request.user}")

        # Verificar que sea método POST
        if request.method != "POST":
            log.error(f"Método no permitido: {request.method}")
            return JsonResponse({"error": "Método no permitido"}, status=405)

        # Obtener empresa del usuario
        try:
            empresa = Empresa.objects.get(user=request.user)
            log.info(f"Empresa encontrada: {empresa}")
        except Empresa.DoesNotExist:
            empresa, created = Empresa.objects.get_or_create(
                user=request.user,
                defaults={"nombre_taller": f"Taller de {request.user.username}"},
            )
            log.info(f"Empresa {'creada' if created else 'encontrada'}: {empresa}")

        # Obtener query desde el JSON del request
        data = json.loads(request.body)
        query = data.get("query", "").strip()
        log.info(f"Query recibida: '{query}'")

        # Filtrar repuestos por empresa del usuario
        repuestos = Repuesto.objects.select_related("categoria").filter(empresa=empresa)
        log.info(f"Repuestos base encontrados: {repuestos.count()}")

        # Si hay query, filtrar por múltiples campos
        if query:
            repuestos = repuestos.filter(
                models.Q(nombre__icontains=query)
                | models.Q(part_number__icontains=query)
                | models.Q(categoria__nombre__icontains=query)
                | models.Q(proveedor__icontains=query)
            )
            log.info(f"Repuestos después del filtro: {repuestos.count()}")

        # Ordenar por nombre
        repuestos = repuestos.order_by("nombre")[:50]  # Limitar a 50 resultados

        # Obtener país para el contexto del template
        country = "CL"  # default
        if empresa and hasattr(empresa, "pais") and empresa.pais:
            country = empresa.pais
        elif hasattr(request, "country") and request.country:
            country = request.country
        elif request.path.startswith("/us/"):
            country = "US"
        elif request.path.startswith("/cl/"):
            country = "CL"

        # Renderizar template parcial
        html = render_to_string(
            "taller/common/repuestos/tabla_repuestos_ajax.html",
            {"repuestos": repuestos, "country": country, "request": request},
        )

        result = {"html": html, "total": repuestos.count()}
        log.info(f"Enviando respuesta con {result['total']} resultados")
        return JsonResponse(result)

    except Exception as e:
        log.error(f"Error en búsqueda AJAX: {str(e)}")
        import traceback

        log.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({"error": "Error interno del servidor"}, status=500)
