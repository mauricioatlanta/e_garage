"""
Context processor: expone business_modules, nav_items y needs_module_config
a todos los templates de la aplicación.
"""

from taller.services.business_module_service import BusinessModuleService


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
        empresa = getattr(user, "empresa", None)
        if not empresa:
            return {}
        config = getattr(empresa, "config", None)
    except Exception:
        return {}

    url_prefix = _url_prefix_from_request(request)
    active = BusinessModuleService.get_active_modules(config)
    nav_items = BusinessModuleService.get_nav_items(config, url_prefix, request.path)

    return {
        "business_modules": active,
        "nav_items": nav_items,
        "needs_module_config": BusinessModuleService.needs_module_configuration(empresa),
    }
