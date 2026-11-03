from django.http import HttpResponse, JsonResponse
from django.template import loader
from taller.config.country_settings import CountrySettings
from taller.version import get_version

def get_empresa_del_usuario(user):
    if not user.is_authenticated:
        return None
    try:
        empresa = getattr(user, 'empresa', None)
        if empresa:
            return empresa
    except Exception:
        pass
    return None

def dynamic_manifest(request, pais, idioma):
    pais = pais.upper()
    idioma = idioma.lower()
    config = CountrySettings.get_country_config(pais)
    if not config:
        config = CountrySettings.get_country_config("CL")
        pais = "CL"
    base_url = f"/{pais.lower()}/{idioma}/"
    empresa = get_empresa_del_usuario(request.user)
    if empresa:
        nombre_empresa = empresa.nombre_taller or "Mi Taller"
        short_name = nombre_empresa[:12]
        start_url = f"{base_url}dashboard/?pwa=1&e={empresa.slug}"
        scope = f"{base_url}"
        manifest_id = f"/egarage-pwa-{empresa.id}-{empresa.slug}"
        if empresa.logo and hasattr(empresa.logo, 'url'):
            logo_url = empresa.logo.url
            icons = [
                {"src": logo_url, "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
                {"src": logo_url, "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
                {"src": logo_url, "sizes": "384x384", "type": "image/png", "purpose": "any maskable"},
                {"src": "/static/images/egarage_icon_192x192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            ]
        else:
            icons = [
                {"src": "/static/images/egarage_icon_72x72.png", "sizes": "72x72", "type": "image/png", "purpose": "any maskable"},
                {"src": "/static/images/egarage_icon_192x192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
                {"src": "/static/images/egarage_icon_512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
            ]
    else:
        nombre_empresa = f"eGarage - {config.get('name', 'Professional Automotive Management')}"
        short_name = "eGarage"
        start_url = base_url
        scope = "/"
        manifest_id = "/egarage-pwa"
        icons = [
            {"src": "/static/images/egarage_icon_192x192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "/static/images/egarage_icon_512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ]
    manifest_data = {
        "id": manifest_id,
        "name": nombre_empresa,
        "short_name": short_name,
        "description": f"Sistema de gestion para {nombre_empresa}. Control total para tu taller.",
        "start_url": start_url,
        "display": "standalone",
        "background_color": "#0a0e27",
        "theme_color": "#0a0e27",
        "orientation": "portrait-primary",
        "scope": scope,
        "lang": idioma,
        "dir": "ltr",
        "categories": ["business", "productivity", "utilities"],
        "icons": icons,
        "screenshots": [
            {"src": "/static/images/screenshot-mobile.png", "sizes": "540x720", "type": "image/png", "form_factor": "narrow"},
            {"src": "/static/images/screenshot-desktop.png", "sizes": "1288x720", "type": "image/png", "form_factor": "wide"},
        ],
        "shortcuts": [
            {"name": "Dashboard", "short_name": "Dashboard", "description": f"Panel de {short_name}", "url": start_url, "icons": [{"src": icons[0]['src'], "sizes": "96x96"}]},
            {"name": "Documentos", "short_name": "Docs", "description": "Gestionar documentos", "url": f"{base_url}documentos/", "icons": [{"src": icons[0]['src'], "sizes": "96x96"}]},
            {"name": "Clientes", "short_name": "Clientes", "description": "Gestionar clientes", "url": f"{base_url}clientes/", "icons": [{"src": icons[0]['src'], "sizes": "96x96"}]},
        ],
        "share_target": {"action": "/share/", "method": "POST", "enctype": "multipart/form-data", "params": {"title": "title", "text": "text", "url": "url"}},
        "prefer_related_applications": False,
    }
    return JsonResponse(manifest_data)

def dynamic_service_worker(request, pais, idioma):
    template = loader.get_template("pwa/service-worker.js")
    context = {
        "pais": pais,
        "idioma": idioma,
        "start_url": f"{pais.lower()}/{idioma.lower()}/",
        "version": get_version(),
    }
    response = HttpResponse(template.render(context), content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    return response
