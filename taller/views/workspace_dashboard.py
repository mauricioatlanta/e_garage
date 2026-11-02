from django.shortcuts import redirect, render
from django.urls import reverse

from taller.auth.decorators import country_login_required
from taller.constants.product_profiles import (
    PRODUCT_CASA_REPUESTOS,
    PRODUCT_DESARMADURIA,
    PRODUCT_RECYCLING,
)
from taller.constants.workspaces import (
    WGT_KPI_DESARM_AVAIL,
    WGT_KPI_DESARM_DEPLETED,
    WGT_KPI_PARTS_COUNT,
    WGT_KPI_PARTS_SOLD_TODAY,
    WGT_KPI_QUOTES_PENDING,
)
from taller.services.workspace_alerts_service import WorkspaceAlertsService
from taller.services.workspace_dashboard_service import WorkspaceDashboardService
from taller.services.workspace_service import WorkspaceService
from taller.utils.empresa import get_or_create_empresa
from taller.views_ingreso import _workspace_prefix_from_request


def _docs_ns_from_request(request) -> str:
    """Return the documentos URL namespace for the current country."""
    path = request.path
    if path.startswith("/us/"):
        return "documentos_us_en"
    if path.startswith("/ar/"):
        return "documentos_ar_es"
    if path.startswith("/uy/"):
        return "documentos_uy_es"
    return "documentos_cl_es"


def _inject_desarm_widget_urls(widgets: list, prefix: str, docs_ns: str, today) -> None:
    """
    Injects navigable URLs into DESARMADURIA KPI widgets.

    Each URL lands on a list view pre-filtered to match exactly what the KPI counts:
      DESARM_AVAIL    → vehicles list filtered to INGRESADO,DESARMANDO
      DESARM_DEPLETED → vehicles list filtered to AGOTADO
      PARTS_SOLD_TODAY→ document list filtered to EMITIDO + today's date
      PARTS_COUNT     → repuesto (bodega) inventory list
    """
    today_str = today.isoformat() if hasattr(today, "isoformat") else str(today)
    docs_base = reverse(f"{docs_ns}:lista_documentos")

    url_map = {
        WGT_KPI_DESARM_AVAIL:    f"{prefix}/desarme/vehiculos/?estado=INGRESADO,DESARMANDO",
        WGT_KPI_DESARM_DEPLETED:  f"{prefix}/desarme/vehiculos/?estado=AGOTADO",
        WGT_KPI_PARTS_SOLD_TODAY: f"{docs_base}?estado=EMITIDO&desde={today_str}&hasta={today_str}",
        WGT_KPI_PARTS_COUNT:      f"{prefix}/repuestos/",
    }

    for widget in widgets:
        url = url_map.get(widget["key"])
        if url is not None:
            widget["url"] = url


@country_login_required
def workspace_dashboard(request):
    empresa = get_or_create_empresa(request)
    config = getattr(empresa, "config", None)
    ws_def = WorkspaceService.get_workspace_def(config)
    prefix = _workspace_prefix_from_request(request)

    if ws_def.product_key == PRODUCT_RECYCLING:
        # RECYCLING has its own fully-built dashboard (KPIs, charts, recent
        # compras/ventas) at taller/reciclaje/ — the generic widget system
        # below only knows about Documento/Repuesto/VehiculoDesarme, none of
        # which apply to a reciclaje business.
        return redirect(f"{prefix}/reciclaje/")

    dashboard_data = WorkspaceDashboardService.resolve(ws_def, empresa)
    docs_ns = _docs_ns_from_request(request)

    if ws_def.product_key == PRODUCT_CASA_REPUESTOS:
        search_url = f"{prefix}/repuestos/buscar/"
    else:
        search_url = f"{prefix}/workspace/buscar/"

    # WGT_KPI_QUOTES_PENDING — pending quotes list (TALLER / PARTS workspaces)
    quotes_url = reverse(f"{docs_ns}:lista_documentos") + "?tipo=PRES&estado=BORRADOR,EMITIDO"
    for widget in dashboard_data["widgets"]:
        if widget["key"] == WGT_KPI_QUOTES_PENDING:
            widget["url"] = quotes_url
            break

    # DESARMADURIA — all four KPI cards link to filtered list views
    if ws_def.product_key == PRODUCT_DESARMADURIA:
        _inject_desarm_widget_urls(
            dashboard_data["widgets"], prefix, docs_ns, dashboard_data["date"]
        )

    alerts_data = WorkspaceAlertsService.resolve(ws_def, empresa, prefix)

    briefing_url = (
        f"{prefix}/workspace/briefing/"
        if ws_def.product_key == PRODUCT_DESARMADURIA
        else None
    )

    return render(request, "dashboard/index.html", {
        "dashboard_data": dashboard_data,
        "workspace_search_url": search_url,
        "workspace_base_prefix": prefix,
        "alerts_data": alerts_data,
        "briefing_url": briefing_url,
    })
