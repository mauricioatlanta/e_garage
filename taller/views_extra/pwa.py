from django.http import HttpResponse, JsonResponse
from django.template import loader

from taller.config.country_settings import CountrySettings
from taller.version import get_version


def dynamic_manifest(request, pais=None, idioma=None):
    """
    Genera un manifest.json dinámico basado en país e idioma.
    Mantiene una estructura mínima y consistente para Android/iOS.
    """
    pais = (pais or "cl").upper()
    idioma = (idioma or "es").lower()

    config = CountrySettings.get_country_config(pais) or CountrySettings.get_country_config("CL")
    country_name = config.get("name", "Professional Automotive Management")
    start_url = f"/{pais.lower()}/{idioma}/"

    data = {
        "id": "/egarage-pwa",
        "name": f"eGarage - {country_name}",
        "short_name": "eGarage",
        "description": "Sistema profesional de gestión para talleres automotrices.",
        "start_url": start_url,
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait-primary",
        "background_color": "#0a0e27",
        "theme_color": "#06b6d4",
        "lang": idioma,
        "dir": "ltr",
        "icons": [
            {
                "src": "/static/img/icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable",
            },
            {
                "src": "/static/img/icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable",
            },
        ],
        "shortcuts": [
            {
                "name": "Dashboard",
                "url": start_url,
            },
            {
                "name": "Documentos",
                "url": f"{start_url}documentos/",
            },
            {
                "name": "Clientes",
                "url": f"{start_url}clientes/",
            },
        ],
        "prefer_related_applications": False,
    }

    return JsonResponse(data)


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
