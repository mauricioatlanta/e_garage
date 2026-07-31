from django.shortcuts import render
from django.urls import reverse

from taller.auth.decorators import country_login_required
from taller.constants.product_profiles import PRODUCT_CASA_REPUESTOS
from taller.constants.workspaces import WGT_KPI_QUOTES_PENDING
from taller.services.workspace_dashboard_service import WorkspaceDashboardService
from taller.services.workspace_service import WorkspaceService
from taller.utils.empresa import get_or_create_empresa
from taller.views_ingreso import _workspace_prefix_from_request


@country_login_required
def workspace_dashboard(request):
    empresa = get_or_create_empresa(request)
    config = getattr(empresa, "config", None)
    ws_def = WorkspaceService.get_workspace_def(config)
    dashboard_data = WorkspaceDashboardService.resolve(ws_def, empresa)
    prefix = _workspace_prefix_from_request(request)

    if ws_def.product_key == PRODUCT_CASA_REPUESTOS:
        search_url = f"{prefix}/repuestos/buscar/"
    else:
        search_url = f"{prefix}/workspace/buscar/"

    # Inject navigable URL into WGT_KPI_QUOTES_PENDING so the card links to
    # the document list pre-filtered to pending quotes (tipo=PRES, both non-final states).
    ns = "documentos_us_en" if request.path.startswith("/us/") else "documentos_cl_es"
    quotes_url = reverse(f"{ns}:lista_documentos") + "?tipo=PRES&estado=BORRADOR,EMITIDO"
    for widget in dashboard_data["widgets"]:
        if widget["key"] == WGT_KPI_QUOTES_PENDING:
            widget["url"] = quotes_url
            break

    return render(request, "dashboard/index.html", {
        "dashboard_data": dashboard_data,
        "workspace_search_url": search_url,
        "workspace_base_prefix": prefix,
    })
