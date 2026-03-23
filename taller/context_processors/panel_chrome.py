"""
Chrome del panel (cabecera + nav): reglas por país/ruta.

USA: tras el login, la mayoría de páginas bajo /us/ usan el layout compacto
tipo Desarme (clase eg-desarme-dashboard-compact en base.html), excepto
Centro de Operaciones (KPIs), que conserva el header amplio.
"""


def us_authenticated_compact_chrome(request):
    """
    True cuando el usuario está autenticado, la URL es workspace USA (/us/...)
    y NO es la página de Centro de Operaciones.

    Nota: ``centro-operaciones-espacial`` no contiene el substring
    ``/centro-operaciones/``, así que sigue usando el chrome compacto.
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"eg_us_panel_compact_chrome": False}

    path = getattr(request, "path", "") or ""
    if not path.startswith("/us/"):
        return {"eg_us_panel_compact_chrome": False}

    # Variante espacial: sigue con chrome compacto (solo excluimos el dashboard KPI).
    if "centro-operaciones-espacial" in path:
        return {"eg_us_panel_compact_chrome": True}

    if "/centro-operaciones/" in path or path.rstrip("/").endswith("/centro-operaciones"):
        return {"eg_us_panel_compact_chrome": False}

    return {"eg_us_panel_compact_chrome": True}
