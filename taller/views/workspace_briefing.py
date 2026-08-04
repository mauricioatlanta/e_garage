"""
taller/views/workspace_briefing.py — Workspace AI Briefing endpoint

GET /<prefix>/workspace/briefing/  →  JSON

Only responds for DESARMADURIA workspaces (404 for all others).
Rate limited by @rate_limit("ia_prediccion") + internal daily budget.
"""
from django.http import JsonResponse

from taller.auth.decorators import country_login_required
from taller.constants.product_profiles import PRODUCT_DESARMADURIA
from taller.middleware.rate_limiting import rate_limit
from taller.services.workspace_briefing_service import (
    BriefingContextBuilder,
    WorkspaceBriefingService,
)
from taller.services.workspace_service import WorkspaceService
from taller.utils.empresa import get_or_create_empresa
from taller.views_ingreso import _workspace_prefix_from_request


@country_login_required
@rate_limit("ia_prediccion", per_ip=True, per_user=True)
def workspace_briefing(request):
    empresa = get_or_create_empresa(request)
    config = getattr(empresa, "config", None)
    ws_def = WorkspaceService.get_workspace_def(config)

    if ws_def.product_key != PRODUCT_DESARMADURIA:
        return JsonResponse({"error": "not_supported"}, status=404)

    prefix = _workspace_prefix_from_request(request)
    lang = (getattr(request, "LANGUAGE_CODE", None) or "es")[:2]

    ctx = BriefingContextBuilder.build(empresa, ws_def, prefix, lang)
    result = WorkspaceBriefingService.resolve(ctx)

    return JsonResponse({
        "greeting":        result.greeting,
        "summary":         list(result.summary),
        "recommendation":  result.recommendation,
        "source":          result.source,
        "cached":          result.cached,
        "generated_at":    result.generated_at,
        "model":           result.model,
        "prompt_version":  result.prompt_version,
    })
