from django.shortcuts import render

from taller.auth.decorators import country_login_required
from taller.services.workspace_dashboard_service import WorkspaceDashboardService
from taller.services.workspace_service import WorkspaceService
from taller.utils.empresa import get_or_create_empresa


@country_login_required
def workspace_dashboard(request):
    empresa = get_or_create_empresa(request)
    config = getattr(empresa, "config", None)
    ws_def = WorkspaceService.get_workspace_def(config)
    dashboard_data = WorkspaceDashboardService.resolve(ws_def, empresa)
    return render(request, "dashboard/index.html", {"dashboard_data": dashboard_data})
