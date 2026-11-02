"""
Contexto processors para la ayuda contextual
"""

from django.urls import resolve

from taller.help.configs import FAQS, PASOS_RECOMENDADOS


def ayuda_contextual(request):
    """
    Agrega ayuda contextual al contexto basado en la URL actual
    """
    ayuda = {"faqs": [], "pasos": [], "mostrar_ayuda": False}

    try:
        # Resolver la URL actual
        resolved = resolve(request.path)
        app_name = resolved.app_name or ""
        url_name = resolved.url_name or ""

        # Determinar módulo basado en la URL
        modulo = None
        if "cliente" in url_name or "clientes" in app_name:
            modulo = "clientes"
        elif "vehiculo" in url_name or "vehiculos" in app_name:
            modulo = "vehiculos"
        elif "documento" in url_name or "documentos" in app_name:
            modulo = "taller"
        elif "dashboard" in url_name:
            modulo = "dashboard"
        elif "settings" in url_name or "configuracion" in url_name:
            modulo = "ajustes"

        if modulo and modulo in FAQS:
            ayuda["faqs"] = FAQS[modulo]
            ayuda["mostrar_ayuda"] = True

        if modulo and modulo in PASOS_RECOMENDADOS:
            ayuda["pasos"] = PASOS_RECOMENDADOS[modulo]
            ayuda["mostrar_ayuda"] = True

        # Agregar información adicional
        ayuda["modulo_actual"] = modulo
        ayuda["url_name"] = url_name

    except Exception:
        # Si hay error resolviendo la URL, no mostrar ayuda
        pass

    return {"ayuda_contextual": ayuda}
