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


def us_signup_slim_header(request):
    """
    Registro USA en /us/signup/ (EN) y /us/es/signup/ (ES): cabecera mínima en base.html
    con idioma y login, sin el chrome completo del panel.

    Prioridad: marca puesta por middleware/vista (``eg_us_public_signup_lang``), luego path.
    """
    lang = getattr(request, "eg_us_public_signup_lang", None)
    if lang in ("en", "es"):
        return {"eg_us_signup_slim_header": True, "eg_us_signup_lang": lang}
    p = (getattr(request, "path", "") or "").rstrip("/") or "/"
    if p not in ("/us/signup", "/us/es/signup"):
        return {
            "eg_us_signup_slim_header": False,
            "eg_us_signup_lang": None,
        }
    return {
        "eg_us_signup_slim_header": True,
        "eg_us_signup_lang": "es" if p == "/us/es/signup" else "en",
    }
