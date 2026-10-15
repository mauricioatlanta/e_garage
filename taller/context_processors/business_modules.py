"""
Context processor: expone business_modules, nav_items, workspace y claves de
navegación a todos los templates de la aplicación.

workspace  → dict resuelto por WorkspaceService (0 queries ORM).
             Disponible en cualquier template. Contiene brand, nav, widget_keys,
             quick_actions y theme del producto activo.
dashboard_data NO se expone aquí; el dashboard view lo agrega al contexto
             explícitamente para no ejecutar queries en requests no-dashboard.
"""

from taller.services.business_module_service import BusinessModuleService
from taller.services.empresa_service import get_empresa_safe
from taller.services.workspace_service import WorkspaceService


def _support_config(request, config):
    """Return an in-memory config override for the superuser support bar."""
    user = getattr(request, "user", None)
    session = getattr(request, "session", {})
    support_rubro = session.get("support_rubro")
    if not getattr(user, "is_superuser", False) or not support_rubro:
        return config

    if config is None:
        from types import SimpleNamespace

        return SimpleNamespace(
            rubro_principal=support_rubro,
            rubros=[],
            usa_vehiculos=True,
            usa_servicios=True,
        )

    # Avoid mutating the ORM instance or writing support state to the tenant.
    from copy import copy

    override = copy(config)
    override.rubro_principal = support_rubro
    override.rubros = []
    return override


def _url_prefix_from_request(request) -> str:
    """Extrae el prefijo /país/lang del path actual (ej: /cl/es)."""
    path = (request.path or "").lstrip("/")
    parts = path.split("/", 2)
    if len(parts) >= 2 and len(parts[0]) == 2 and len(parts[1]) == 2:
        return f"/{parts[0]}/{parts[1]}"
    return "/cl/es"


def business_modules(request):
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return {}

    try:
        empresa = get_empresa_safe(request)
        config = _support_config(request, getattr(empresa, "config", None) if empresa else None)
    except Exception:
        config = _support_config(request, None)
        empresa = None

    if config is None:
        return {}

    url_prefix = _url_prefix_from_request(request)
    active = BusinessModuleService.get_active_modules(config)
    nav_items = BusinessModuleService.get_nav_items(config, url_prefix, request.path)

    # Workspace resuelto: 0 queries ORM, labels i18n, URLs completas.
    workspace = WorkspaceService.resolve(config, url_prefix, request.path)

    return {
        "business_modules":   active,
        "nav_items":          workspace["nav"],   # workspace nav replaces old nav_items
        "needs_module_config": BusinessModuleService.needs_module_configuration(empresa) if empresa else False,
        "product_profile":    BusinessModuleService.get_product_profile(config),
        "nav_url_prefix":     url_prefix,
        "workspace":          workspace,
        "support_environment_active": bool(
            getattr(user, "is_superuser", False)
            and getattr(request, "session", {}).get("support_rubro")
        ),
        "support_rubro": getattr(request, "session", {}).get("support_rubro", ""),
    }
