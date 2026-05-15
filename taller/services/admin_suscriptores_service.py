import logging

from django.core.paginator import Paginator
from django.db.models import Q

from taller.models.empresa import Empresa
from taller.utils.country_config import COUNTRY_SETTINGS

logger = logging.getLogger(__name__)

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
        "dias",
        "-dias",
    }
)


def _next_ord_value(current: str, field: str) -> str:
    if current == field:
        return f"-{field}"
    if current == f"-{field}":
        return field
    return field


def _sort_querystring(params, new_ord: str) -> str:
    q = params.copy()
    q["ord"] = new_ord
    q.pop("page", None)
    return "?" + q.urlencode()


def _estado_sort_rank(empresa: Empresa) -> int:
    return {"vencida": 0, "critico": 1, "advertencia": 2, "activa": 3}.get(
        empresa.estado_suscripcion, 9
    )


def _apply_empresas_sort(empresas_list: list, ord_param: str) -> None:
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
    elif ord_param == "dias":
        empresas_list.sort(key=lambda e: e.dias_restantes if e.dias_restantes is not None else -1)
    elif ord_param == "-dias":
        empresas_list.sort(
            key=lambda e: e.dias_restantes if e.dias_restantes is not None else -1,
            reverse=True,
        )
    else:
        empresas_list.sort(key=lambda e: e.dias_restantes if e.dias_restantes is not None else 0)


def get_admin_suscriptores_queryset(incluir_bajas: bool = False):
    queryset = Empresa.objects.select_related("user", "user__suscripcion").filter(
        user__isnull=False
    )
    if not incluir_bajas:
        queryset = queryset.filter(user__is_active=True)
    return queryset


def apply_admin_suscriptores_filters(qs, filters: dict):
    pais_filter = filters.get("pais", "")
    status_filter = filters.get("status", "")
    search_query = filters.get("search", "")

    if pais_filter:
        qs = qs.filter(pais=pais_filter)

    if status_filter == "activa":
        qs = qs.filter(suscripcion_activa=True)
    elif status_filter == "vencida":
        qs = qs.filter(suscripcion_activa=False)
    elif status_filter == "trial":
        qs = qs.filter(plan="trial")

    if search_query:
        qs = qs.filter(
            Q(nombre_taller__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(telefono__icontains=search_query)
        )

    return qs


def build_admin_suscriptores_stats(incluir_bajas: bool = False) -> dict:
    base_qs = Empresa.objects.filter(user__isnull=False)
    if not incluir_bajas:
        base_qs = base_qs.filter(user__is_active=True)

    total_empresas = base_qs.count()
    empresas_activas = base_qs.filter(suscripcion_activa=True).count()
    empresas_vencidas = base_qs.filter(suscripcion_activa=False).count()

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

    return {
        "total_empresas": total_empresas,
        "empresas_activas": empresas_activas,
        "empresas_vencidas": empresas_vencidas,
        "stats_por_pais": stats_por_pais,
    }


def build_admin_suscriptores_dashboard(request):
    pais_filter = request.GET.get("pais", "")
    status_filter = request.GET.get("status", "")
    dias_filter = request.GET.get("dias", "")
    search_query = request.GET.get("search", "")
    ord_raw = (request.GET.get("ord") or "").strip()
    ord_param = ord_raw if ord_raw in _ALLOWED_ORD else ""
    incluir_bajas = request.GET.get("incluir_bajas") == "1"

    filters = {
        "pais": pais_filter,
        "status": status_filter,
        "dias": dias_filter,
        "search": search_query,
    }

    queryset = get_admin_suscriptores_queryset(incluir_bajas)
    filtered_qs = apply_admin_suscriptores_filters(queryset, filters)

    empresas_list = []
    for empresa in filtered_qs:
        try:
            _ = empresa.dias_restantes
            _ = empresa.estado_suscripcion
            empresas_list.append(empresa)
        except (AttributeError, TypeError, ValueError) as exc:
            logger.warning("Error procesando empresa %s: %s", empresa.id, exc)
            continue

    if dias_filter == "critico":
        empresas_list = [e for e in empresas_list if e.estado_suscripcion == "critico"]
    elif dias_filter == "advertencia":
        empresas_list = [e for e in empresas_list if e.estado_suscripcion == "advertencia"]
    elif dias_filter == "vencido":
        empresas_list = [e for e in empresas_list if e.estado_suscripcion == "vencida"]

    _apply_empresas_sort(empresas_list, ord_param)

    sort_href = {
        field: _sort_querystring(request.GET, _next_ord_value(ord_param, field))
        for field in ("empresa", "pais", "plan", "estado")
    }

    paginator = Paginator(empresas_list, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    stats = build_admin_suscriptores_stats(incluir_bajas)

    empresas_criticas = []
    crit_qs = get_admin_suscriptores_queryset(incluir_bajas)
    for empresa in crit_qs:
        try:
            dias = empresa.dias_restantes
            if dias is not None and 0 < dias < 5:
                empresas_criticas.append(empresa)
        except (AttributeError, TypeError, ValueError):
            continue

    context = {
        "page_obj": page_obj,
        "empresas": page_obj,
        "pais_filter": pais_filter,
        "status_filter": status_filter,
        "dias_filter": dias_filter,
        "search_query": search_query,
        "ord": ord_param,
        "sort_href": sort_href,
        "incluir_bajas": incluir_bajas,
        "paises": COUNTRY_SETTINGS,
        "empresas_criticas": empresas_criticas,
    }
    context.update(stats)
    return context


def serialize_bulk_action_result(
    success: bool, message: str = "", extra: dict | None = None
) -> dict:
    result = {"success": success, "message": message}
    if extra:
        result.update(extra)
    return result
