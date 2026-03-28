from django.http import HttpResponse, JsonResponse
from django.template import loader
from taller.config.country_settings import CountrySettings
from taller.version import get_version


def dynamic_manifest(request, pais, idioma):
    """
    Genera un manifest.json dinámico basado en el país e idioma de la URL.
    """
    pais = pais.upper()
    idioma = idioma.lower()

    config = CountrySettings.get_country_config(pais)
    if not config:
        # Fallback a Chile si el país no existe
        config = CountrySettings.get_country_config("CL")
        pais = "CL"

    start_url = f"/{pais.lower()}/{idioma}/"

    # Datos básicos del manifest
    manifest_data = {
        "id": "/egarage-pwa",
        "name": f"eGarage - {config.get('name', 'Professional Automotive Management')}",
        "short_name": "eGarage",
        "description": "Sistema profesional de gestión para talleres automotrices. Control total para tu taller.",
        "start_url": start_url,
        "display": "standalone",
        "background_color": "#0a0e27",
        "theme_color": "#0a0e27",
        "orientation": "portrait-primary",
        "scope": "/",
        "lang": idioma,
        "dir": "ltr",
        "categories": ["business", "productivity", "utilities"],
        "icons": [
            {
                "src": "/static/images/egarage_icon_72x72.png",
                "sizes": "72x72",
                "type": "image/png",
                "purpose": "any maskable",
            },
            {
                "src": "/static/images/egarage_icon_96x96.png",
                "sizes": "96x96",
                "type": "image/png",
                "purpose": "any maskable",
            },
            {
                "src": "/static/images/egarage_icon_128x128.png",
                "sizes": "128x128",
                "type": "image/png",
                "purpose": "any maskable",
            },
            {
                "src": "/static/images/egarage_icon_144x144.png",
                "sizes": "144x144",
                "type": "image/png",
                "purpose": "any maskable",
            },
            {
                "src": "/static/images/egarage_icon_152x152.png",
                "sizes": "152x152",
                "type": "image/png",
                "purpose": "any maskable",
            },
            {
                "src": "/static/images/egarage_icon_192x192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable",
            },
            {
                "src": "/static/images/egarage_icon_384x384.png",
                "sizes": "384x384",
                "type": "image/png",
                "purpose": "any maskable",
            },
            {
                "src": "/static/images/egarage_icon_512x512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable",
            },
        ],
        "screenshots": [
            {
                "src": "/static/images/screenshot-mobile.png",
                "sizes": "540x720",
                "type": "image/png",
                "form_factor": "narrow",
            },
            {
                "src": "/static/images/screenshot-desktop.png",
                "sizes": "1280x720",
                "type": "image/png",
                "form_factor": "wide",
            },
        ],
        "shortcuts": [
            {
                "name": "Dashboard",
                "short_name": "Dashboard",
                "description": "Acceso rápido al panel principal",
                "url": start_url,
                "icons": [{"src": "/static/images/egarage_icon_96x96.png", "sizes": "96x96"}],
            },
            {
                "name": "Documentos",
                "short_name": "Docs",
                "description": "Gestionar documentos",
                "url": f"{start_url}documentos/",
                "icons": [{"src": "/static/images/egarage_icon_96x96.png", "sizes": "96x96"}],
            },
            {
                "name": "Clientes",
                "short_name": "Clientes",
                "description": "Gestionar clientes",
                "url": f"{start_url}clientes/",
                "icons": [{"src": "/static/images/egarage_icon_96x96.png", "sizes": "96x96"}],
            },
        ],
        "share_target": {
            "action": "/share/",
            "method": "POST",
            "enctype": "multipart/form-data",
            "params": {"title": "title", "text": "text", "url": "url"},
        },
        "prefer_related_applications": False,
    }

    return JsonResponse(manifest_data)


def dynamic_service_worker(request, pais, idioma):
    """
    Genera un service-worker.js dinámico basado en el país e idioma de la URL.
    """
    template = loader.get_template("pwa/service-worker.js")
    context = {
        "pais": pais,
        "idioma": idioma,
        "start_url": f"/{pais.lower()}/{idioma.lower()}/",
        "version": get_version(),
    }
    response = HttpResponse(template.render(context), content_type="application/javascript")
    # Permitir que el Service Worker tenga un scope superior al de su ubicación
    response["Service-Worker-Allowed"] = "/"
    return response
