"""
Panel de Administración de Suscriptores
========================================

Vista administrativa para gestionar suscriptores:
- Listar suscriptores por país
- Ver status y días restantes
- Extender suscripciones
- Enviar notificaciones (email + WhatsApp)
"""

import logging
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from taller.models.empresa import Empresa
from taller.models.suscripcion import Suscripcion
from taller.utils.country_config import COUNTRY_SETTINGS

logger = logging.getLogger(__name__)

# Ordenación lista suscriptores (?ord=…)
_ALLOWED_ORD = frozenset(
    {
        "empresa",
        "-empresa",
        "pais",
        "-pais",
        "plan",
        "-plan",
        "estado",
        "-estado",
        "fecha",
        "-fecha",
        "dias",
        "-dias",
    }
)


def _next_ord_value(current: str, field: str) -> str:
    """Alterna asc / desc al pulsar el mismo encabezado."""
    if current == field:
        return f"-{field}"
    if current == f"-{field}":
        return field
    return field


def _sort_querystring(request, new_ord: str) -> str:
    q = request.GET.copy()
    q["ord"] = new_ord
    q.pop("page", None)
    return "?" + q.urlencode()


def _page_querystring(request, page_number: int) -> str:
    q = request.GET.copy()
    q["page"] = page_number
    return "?" + q.urlencode()


def _estado_sort_rank(empresa: Empresa) -> int:
    return {"vencida": 0, "critico": 1, "advertencia": 2, "activa": 3}.get(
        empresa.estado_suscripcion, 9
    )


def _subscription_started_at(empresa: Empresa):
    """Fecha visible de alta/suscripción para el panel admin."""
    suscripcion = getattr(getattr(empresa, "user", None), "suscripcion", None)
    return (
        getattr(suscripcion, "fecha_inicio", None)
        or getattr(empresa, "fecha_inicio", None)
        or getattr(getattr(empresa, "user", None), "date_joined", None)
    )


def _date_sort_value(value) -> int:
    if not value:
        return 0
    if isinstance(value, datetime):
        return value.date().toordinal()
    if isinstance(value, date):
        return value.toordinal()
    return 0


def _apply_empresas_sort(empresas_list: list, ord_param: str) -> None:
    """Ordena in-place la lista de empresas (ya materializada)."""
    if ord_param == "empresa":
        empresas_list.sort(key=lambda e: (e.nombre_taller or "").lower())
    elif ord_param == "-empresa":
        empresas_list.sort(key=lambda e: (e.nombre_taller or "").lower(), reverse=True)
    elif ord_param == "pais":
        empresas_list.sort(key=lambda e: (e.pais or "").upper())
    elif ord_param == "-pais":
        empresas_list.sort(key=lambda e: (e.pais or "").upper(), reverse=True)
    elif ord_param == "plan":
        empresas_list.sort(key=lambda e: (e.plan or "").lower())
    elif ord_param == "-plan":
        empresas_list.sort(key=lambda e: (e.plan or "").lower(), reverse=True)
    elif ord_param == "estado":
        empresas_list.sort(key=_estado_sort_rank)
    elif ord_param == "-estado":
        empresas_list.sort(key=_estado_sort_rank, reverse=True)
    elif ord_param == "fecha":
        empresas_list.sort(key=lambda e: _date_sort_value(getattr(e, "admin_fecha_suscripcion", None)))
    elif ord_param == "-fecha":
        empresas_list.sort(
            key=lambda e: _date_sort_value(getattr(e, "admin_fecha_suscripcion", None)),
            reverse=True,
        )
    elif ord_param == "dias":
        empresas_list.sort(key=lambda e: e.dias_restantes if e.dias_restantes is not None else -1)
    elif ord_param == "-dias":
        empresas_list.sort(
            key=lambda e: e.dias_restantes if e.dias_restantes is not None else -1,
            reverse=True,
        )
    else:
        empresas_list.sort(key=lambda e: e.dias_restantes if e.dias_restantes is not None else 0)


@staff_member_required
def admin_suscriptores(request):
    """
    Panel principal de administración de suscriptores

    Filtros:
    - Por país (CL, US, MX, PE, CO, EC, BR, VE)
    - Por status (activa, vencida, trial)
    - Por días restantes (crítico < 5, bajo < 15, normal)
    """
    try:
        # Obtener filtros de la URL
        pais_filter = request.GET.get("pais", "")
        status_filter = request.GET.get("status", "")
        dias_filter = request.GET.get("dias", "")
        search_query = request.GET.get("search", "")
        ord_raw = (request.GET.get("ord") or "").strip()
        ord_param = ord_raw if ord_raw in _ALLOWED_ORD else ""
        # Tras "Eliminar" en panel: user.is_active=False (baja lógica). Por defecto no listar esas filas.
        incluir_bajas = request.GET.get("incluir_bajas") == "1"

        # Obtener todas las empresas con sus usuarios y suscripciones
        # Suscripcion está relacionada con User, no directamente con Empresa
        # Filtrar empresas que tienen usuario para evitar errores
        try:
            empresas = Empresa.objects.select_related("user", "user__suscripcion").filter(
                user__isnull=False
            )
            if not incluir_bajas:
                empresas = empresas.filter(user__is_active=True)
        except Exception as e:
            logger.error(f"Error al obtener empresas: {e}", exc_info=True)
            # Si hay error con select_related, intentar sin él
            empresas = Empresa.objects.filter(user__isnull=False)
            if not incluir_bajas:
                empresas = empresas.filter(user__is_active=True)

        # Aplicar filtros
        if pais_filter:
            empresas = empresas.filter(pais=pais_filter)

        if status_filter == "activa":
            empresas = empresas.filter(suscripcion_activa=True)
        elif status_filter == "vencida":
            empresas = empresas.filter(suscripcion_activa=False)
        elif status_filter == "trial":
            empresas = empresas.filter(plan="trial")

        # Búsqueda por nombre de taller, email o teléfono (aplicar antes de convertir a lista)
        if search_query:
            empresas = empresas.filter(
                Q(nombre_taller__icontains=search_query)
                | Q(user__email__icontains=search_query)
                | Q(telefono__icontains=search_query)
            )

        # Convertir a lista para poder usar propiedades como estado_suscripcion
        # Agregar manejo de errores para empresas con datos inconsistentes
        empresas_list = []
        for empresa in empresas:
            try:
                # Verificar que la empresa tenga los datos necesarios
                _ = empresa.dias_restantes
                _ = empresa.estado_suscripcion
                empresa.admin_fecha_suscripcion = _subscription_started_at(empresa)
                empresas_list.append(empresa)
            except (AttributeError, TypeError, ValueError) as e:
                # Si hay un error con alguna empresa, loguear y continuar
                logger.warning(f"Error procesando empresa {empresa.id}: {e}")
                continue

        if dias_filter == "critico":
            # Crítico: 1 día o menos (pero no vencido)
            empresas_list = [e for e in empresas_list if e.estado_suscripcion == "critico"]
        elif dias_filter == "advertencia":
            # Advertencia: entre 1 y 5 días
            empresas_list = [e for e in empresas_list if e.estado_suscripcion == "advertencia"]
        elif dias_filter == "vencido":
            # Vencido: debe_bloquear = True
            empresas_list = [e for e in empresas_list if e.estado_suscripcion == "vencida"]

        _apply_empresas_sort(empresas_list, ord_param)
        empresas = empresas_list

        sort_href = {
            field: _sort_querystring(request, _next_ord_value(ord_param, field))
            for field in ("empresa", "pais", "plan", "fecha", "estado")
        }

        # Paginación
        paginator = Paginator(empresas, 25)  # 25 por página (empresas ya es una lista ordenada)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        previous_page_url = (
            _page_querystring(request, page_obj.previous_page_number())
            if page_obj.has_previous()
            else ""
        )
        next_page_url = (
            _page_querystring(request, page_obj.next_page_number()) if page_obj.has_next() else ""
        )

        # Estadísticas generales (mismo alcance que el listado: usuarios activos salvo ?incluir_bajas=1)
        _stats_base = Empresa.objects.filter(user__isnull=False)
        if not incluir_bajas:
            _stats_base = _stats_base.filter(user__is_active=True)
        total_empresas = _stats_base.count()
        empresas_activas = _stats_base.filter(suscripcion_activa=True).count()
        empresas_vencidas = _stats_base.filter(suscripcion_activa=False).count()

        # Estadísticas por país
        stats_por_pais = {}
        for codigo, config in COUNTRY_SETTINGS.items():
            q_pais = Empresa.objects.filter(pais=codigo, user__isnull=False)
            if not incluir_bajas:
                q_pais = q_pais.filter(user__is_active=True)
            stats_por_pais[codigo] = {
                "nombre": config.get("name", codigo),
                "total": q_pais.count(),
                "activas": q_pais.filter(suscripcion_activa=True).count(),
                "vencidas": q_pais.filter(suscripcion_activa=False).count(),
            }

        # Empresas críticas (menos de 5 días) - solo empresas con usuario activo en panel
        empresas_criticas = []
        _crit_qs = Empresa.objects.filter(user__isnull=False)
        if not incluir_bajas:
            _crit_qs = _crit_qs.filter(user__is_active=True)
        for e in _crit_qs:
            try:
                dias = e.dias_restantes
                if dias is not None and 0 < dias < 5:
                    empresas_criticas.append(e)
            except (AttributeError, TypeError, ValueError):
                continue

        context = {
            "page_obj": page_obj,
            "previous_page_url": previous_page_url,
            "next_page_url": next_page_url,
            "empresas": page_obj,
            "pais_filter": pais_filter,
            "status_filter": status_filter,
            "dias_filter": dias_filter,
            "search_query": search_query,
            "ord": ord_param,
            "sort_href": sort_href,
            "incluir_bajas": incluir_bajas,
            "paises": COUNTRY_SETTINGS,
            "stats_por_pais": stats_por_pais,
            "total_empresas": total_empresas,
            "empresas_activas": empresas_activas,
            "empresas_vencidas": empresas_vencidas,
            "empresas_criticas": empresas_criticas,
        }

        return render(request, "admin/suscriptores/lista_suscriptores.html", context)
    except Exception as e:
        logger.error(f"Error en admin_suscriptores: {e}", exc_info=True)
        from django.http import HttpResponse

        error_message = f"Error al cargar el panel de suscriptores: {str(e)}. Por favor, contacta al administrador."
        return HttpResponse(
            f"<html><body><h1>Error 400 - Bad Request</h1><p>{error_message}</p></body></html>",
            status=400,
            content_type="text/html",
        )


@staff_member_required
@require_http_methods(["POST"])
def extender_suscripcion_ajax(request, empresa_id):
    """
    Vista AJAX para extender suscripción de una empresa

    ✅ USA: Empresa.admin_grant_courtesy_extension() que incluye:
    - Auditoría automática
    - Notificaciones automáticas (email + WhatsApp)
    - Validación de duraciones (1, 6, 12 meses)
    - Registro de logs

    Parámetros POST:
    - meses: Número de meses a extender (1, 6, 12) - NOTA: Solo acepta 1, 6 o 12
    - enviar_notificacion: 'true' o 'false' (opcional, default: true)
    """
    empresa = get_object_or_404(Empresa, id=empresa_id)

    try:
        meses = int(request.POST.get("meses", 1))
        enviar_notificacion = request.POST.get("enviar_notificacion", "true").lower() == "true"

        # ✅ Validar duraciones permitidas (1, 6, 12 meses según admin_grant_courtesy_extension)
        if meses not in [1, 6, 12]:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Meses inválidos. Debe ser 1, 6 o 12 meses (según admin_grant_courtesy_extension).",
                },
                status=400,
            )

        # ✅ USAR admin_grant_courtesy_extension que incluye:
        # - Extensión de fecha
        # - Actualización de estado
        # - Auditoría automática
        # - Notificaciones automáticas (si está configurado)
        resultado = Empresa.admin_grant_courtesy_extension(
            user_email=empresa.user.email,
            duration_months=meses,
            reason=f"Cortesía eGarage - Extendido por {request.user.username}",
            admin_user=request.user,
        )

        # ✅ admin_grant_courtesy_extension() ya envía notificaciones automáticamente
        # a través de notificar_renovacion_exitosa() con is_courtesy=True
        # NO es necesario enviar notificaciones manualmente
        nueva_fecha_fin = resultado.get("nueva_fecha_fin")

        if not nueva_fecha_fin:
            return JsonResponse(
                {
                    "success": False,
                    "error": "No se pudo obtener la nueva fecha de expiración del resultado",
                },
                status=500,
            )

        empresa.refresh_from_db()  # Refrescar para obtener datos actualizados

        # Actualizar suscripción si existe
        try:
            suscripcion = empresa.user.suscripcion
            if suscripcion:
                suscripcion.fecha_fin = (
                    nueva_fecha_fin.date() if hasattr(nueva_fecha_fin, "date") else nueva_fecha_fin
                )
                suscripcion.activa = True
                suscripcion.save()
        except Suscripcion.DoesNotExist:
            pass
        except Exception as e:
            # No fallar si hay un error actualizando la suscripción, solo loguear
            logger.warning(f"Error actualizando suscripción después de extender: {e}")

        # Formatear fecha para la respuesta
        fecha_fin_str = (
            nueva_fecha_fin.strftime("%Y-%m-%d")
            if hasattr(nueva_fecha_fin, "strftime")
            else str(nueva_fecha_fin)
        )

        return JsonResponse(
            {
                "success": True,
                "message": f"✅ Extensión de cortesía otorgada exitosamente por {meses} mes(es). Notificaciones enviadas automáticamente.",
                "nueva_fecha_fin": fecha_fin_str,
                "dias_restantes": empresa.dias_restantes,
                "notificaciones_enviadas": True,  # admin_grant_courtesy_extension siempre envía notificaciones
                "empresa": resultado.get("empresa", empresa.nombre_taller),
            }
        )

    except ValueError as e:
        # admin_grant_courtesy_extension lanza ValueError para errores de validación
        return JsonResponse({"success": False, "error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error extendiendo suscripción: {e}", exc_info=True)
        return JsonResponse(
            {"success": False, "error": f"Error al extender suscripción: {str(e)}"}, status=500
        )


@staff_member_required
def detalle_suscriptor(request, empresa_id):
    """
    Vista de detalle de un suscriptor específico
    """
    empresa = get_object_or_404(
        Empresa.objects.select_related("user", "user__suscripcion"), id=empresa_id
    )

    # Obtener suscripción si existe
    try:
        suscripcion = empresa.user.suscripcion
    except Suscripcion.DoesNotExist:
        suscripcion = None

    context = {
        "empresa": empresa,
        "suscripcion": suscripcion,
        "dias_restantes": empresa.dias_restantes,
        "config_pais": COUNTRY_SETTINGS.get(empresa.pais, COUNTRY_SETTINGS["CL"]),
    }

    return render(request, "admin/suscriptores/detalle_suscriptor.html", context)


@staff_member_required
@require_http_methods(["POST"])
def actualizar_telefono_ajax(request, empresa_id):
    """
    Vista AJAX para actualizar el teléfono de una empresa

    Parámetros POST:
    - telefono: Nuevo número de teléfono
    """
    empresa = get_object_or_404(Empresa, id=empresa_id)

    try:
        nuevo_telefono = request.POST.get("telefono", "").strip()

        # Validar que el teléfono no sea demasiado largo
        if len(nuevo_telefono) > 32:
            return JsonResponse(
                {"success": False, "error": "El teléfono no puede tener más de 32 caracteres."},
                status=400,
            )

        # Actualizar teléfono
        empresa.telefono = nuevo_telefono
        empresa.save()

        logger.info(
            f"Teléfono actualizado para empresa {empresa.id} ({empresa.nombre_taller}): {nuevo_telefono}"
        )

        return JsonResponse(
            {
                "success": True,
                "message": "✅ Teléfono actualizado exitosamente.",
                "telefono": empresa.telefono,
            }
        )

    except Exception as e:
        logger.error(f"Error actualizando teléfono: {e}", exc_info=True)
        return JsonResponse(
            {"success": False, "error": f"Error al actualizar teléfono: {str(e)}"}, status=500
        )


@staff_member_required
@require_http_methods(["POST"])
def desactivar_suscripcion_ajax(request, empresa_id):
    """
    Desactiva la suscripción comercial (empresa.suscripcion_activa=False).
    No elimina usuario ni datos; el acceso puede quedar bloqueado por middleware.
    """
    empresa = get_object_or_404(Empresa.objects.select_related("user"), id=empresa_id)

    try:
        empresa.suscripcion_activa = False
        empresa.save(update_fields=["suscripcion_activa"])

        try:
            suscripcion = empresa.user.suscripcion
            if suscripcion:
                suscripcion.activa = False
                suscripcion.save(update_fields=["activa"])
        except Suscripcion.DoesNotExist:
            pass
        except Exception as ex:
            logger.warning(
                "Suscripción no actualizada al desactivar empresa %s: %s", empresa_id, ex
            )

        logger.info(
            "Admin %s desactivó suscripción empresa_id=%s (%s)",
            getattr(request.user, "pk", None),
            empresa_id,
            empresa.nombre_taller,
        )
        return JsonResponse(
            {
                "success": True,
                "message": "Suscripción desactivada correctamente.",
            }
        )
    except Exception as e:
        logger.error("Error desactivando suscripción %s: %s", empresa_id, e, exc_info=True)
        return JsonResponse(
            {"success": False, "error": f"No se pudo desactivar: {str(e)}"},
            status=500,
        )


@staff_member_required
@require_http_methods(["POST"])
def eliminar_suscriptor_ajax(request, empresa_id):
    """
    Baja lógica: desactiva el usuario (is_active=False) y la suscripción.
    No borra filas de Empresa/User (evita pérdida de datos y efectos en cascada no deseados).
    """
    empresa = get_object_or_404(Empresa.objects.select_related("user"), id=empresa_id)
    user = empresa.user

    try:
        user.is_active = False
        user.save(update_fields=["is_active"])

        empresa.suscripcion_activa = False
        empresa.save(update_fields=["suscripcion_activa"])

        try:
            suscripcion = user.suscripcion
            if suscripcion:
                suscripcion.activa = False
                suscripcion.save(update_fields=["activa"])
        except Suscripcion.DoesNotExist:
            pass
        except Exception as ex:
            logger.warning(
                "Suscripción no actualizada al dar de baja empresa %s: %s", empresa_id, ex
            )

        logger.warning(
            "Admin %s dio de baja lógica usuario empresa_id=%s email=%s",
            getattr(request.user, "pk", None),
            empresa_id,
            getattr(user, "email", ""),
        )
        return JsonResponse(
            {
                "success": True,
                "message": "Usuario desactivado y suscripción cerrada (baja lógica).",
            }
        )
    except Exception as e:
        logger.error("Error en baja lógica suscriptor %s: %s", empresa_id, e, exc_info=True)
        return JsonResponse(
            {"success": False, "error": f"No se pudo completar la baja: {str(e)}"},
            status=500,
        )
