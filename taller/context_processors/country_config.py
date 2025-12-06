"""
Context processor para exponer configuración de país en todos los templates.

Usa CountrySettings para centralizar la lógica de país/idioma/impuestos.
"""

from taller.config.country_settings import CountrySettings


def country_context(request):
    """
    Expone configuración de país en el contexto de todos los templates.

    Variables disponibles en templates:
    - country_code: Código del país (ej: 'CL', 'US', 'PE')
    - country_config: Dict con toda la configuración del país
    - country_name: Nombre del país en español
    - country_name_en: Nombre del país en inglés
    - country_language: Idioma por defecto del país
    - country_currency: Moneda del país
    - country_currency_symbol: Símbolo de la moneda
    - country_tax_rate: Tasa de impuesto (ej: 19.0 para 19%)
    - country_tax_label: Etiqueta del impuesto (ej: 'IVA', 'Sales Tax')
    """
    # Detectar país desde el request (middleware debería setearlo)
    country_code = getattr(request, "country", None) or getattr(request, "country_code", None)

    # Si no está en el request, intentar inferir desde la URL
    if not country_code and hasattr(request, "path"):
        country_code = CountrySettings.get_country_from_url(request.path)

    # Fallback al país por defecto
    if not country_code:
        country_code = CountrySettings.DEFAULT_COUNTRY

    # Normalizar a mayúsculas
    country_code = country_code.upper() if country_code else CountrySettings.DEFAULT_COUNTRY

    # Obtener configuración del país
    config = CountrySettings.get_country_config(country_code)

    # Detectar idioma (desde el request o desde la configuración del país)
    lang_code = getattr(request, "lang_code", None) or getattr(request, "LANGUAGE_CODE", None)
    if not lang_code:
        # Intentar desde la URL
        if hasattr(request, "path"):
            path = request.path.lower()
            if "/en/" in path:
                lang_code = "en"
            elif "/es/" in path:
                lang_code = "es"
            else:
                lang_code = config.get("language", "es")
    else:
        lang_code = lang_code.lower()[:2]  # Normalizar a 2 caracteres

    return {
        "country_code": country_code,
        "country_config": config,
        "country_name": config.get("name_es") or config.get("name", country_code),
        "country_name_en": config.get("name_en") or config.get("name", country_code),
        "country_language": config.get("language", "es"),
        "country_currency": config.get("currency", "USD"),
        "country_currency_symbol": config.get("currency_symbol", "$"),
        "country_tax_rate": config.get("tax_rate", 0.0),
        "country_tax_label": config.get("tax_label", "Tax"),
        "country_timezone": config.get("timezone", "UTC"),
        "country_phone_prefix": config.get("phone_prefix", ""),
        "country_date_format": config.get("date_format", "DD/MM/YYYY"),
        "lang_code": lang_code,
        "url_prefix": config.get("url_prefix", f"/{country_code.lower()}"),
    }



