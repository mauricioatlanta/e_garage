import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

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
            "taller/repuestos/tabla_repuestos_ajax.html",
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
