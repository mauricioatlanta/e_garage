"""
Configuración Centralizada de Países - eGarage
==============================================

Sistema de configuración "Configuration over Code" para soportar 8 países
sin necesidad de if/elif en todo el código.

Uso:
    from taller.utils.country_config import get_country_config

    config = get_country_config('PE')
    print(config['currency'])  # 'PEN'
    print(config['decimals'])  # 2
    print(config['tax_rate'])  # 18.0
"""

from decimal import Decimal

from django.conf import settings

# Configuración completa por país
COUNTRY_SETTINGS = {
    "CL": {
        "currency": "CLP",
        "currency_symbol": "$",
        "decimals": 0,
        "tax_name": "IVA",
        "tax_rate": 19.0,
        "lang": "es",
        "locale": "es-CL",
        "timezone": "America/Santiago",
        "date_format": "DD/MM/YYYY",
        "phone_prefix": "+56",
        "url_prefix": "/cl",
        "namespace": "chile",
    },
    "US": {
        "currency": "USD",
        "currency_symbol": "$",
        "decimals": 2,
        "tax_name": "Sales Tax",
        "tax_rate": 0.0,  # Varía por estado, se calcula dinámicamente
        "lang": "en",
        "locale": "en-US",
        "timezone": "America/New_York",
        "date_format": "MM/DD/YYYY",
        "phone_prefix": "+1",
        "url_prefix": "/us",
        "namespace": "usa",
    },
    "MX": {
        "currency": "MXN",
        "currency_symbol": "$",
        "decimals": 2,
        "tax_name": "IVA",
        "tax_rate": 16.0,
        "lang": "es",
        "locale": "es-MX",
        "timezone": "America/Mexico_City",
        "date_format": "DD/MM/YYYY",
        "phone_prefix": "+52",
        "url_prefix": "/mx",
        "namespace": "mexico",
    },
    "PE": {
        "currency": "PEN",
        "currency_symbol": "S/",
        "decimals": 2,
        "tax_name": "IGV",
        "tax_rate": 18.0,
        "lang": "es",
        "locale": "es-PE",
        "timezone": "America/Lima",
        "date_format": "DD/MM/YYYY",
        "phone_prefix": "+51",
        "url_prefix": "/pe",
        "namespace": "peru",
    },
    "CO": {
        "currency": "COP",
        "currency_symbol": "$",
        "decimals": 0,
        "tax_name": "IVA",
        "tax_rate": 19.0,
        "lang": "es",
        "locale": "es-CO",
        "timezone": "America/Bogota",
        "date_format": "DD/MM/YYYY",
        "phone_prefix": "+57",
        "url_prefix": "/co",
        "namespace": "colombia",
    },
    "EC": {
        "currency": "USD",  # Ecuador usa dólares
        "currency_symbol": "$",
        "decimals": 2,
        "tax_name": "IVA",
        "tax_rate": 12.0,
        "lang": "es",
        "locale": "es-EC",
        "timezone": "America/Guayaquil",
        "date_format": "DD/MM/YYYY",
        "phone_prefix": "+593",
        "url_prefix": "/ec",
        "namespace": "ecuador",
    },
    "BR": {
        "currency": "BRL",
        "currency_symbol": "R$",
        "decimals": 2,
        "tax_name": "ICMS",  # Impuesto sobre Circulação de Mercadorias e Serviços
        "tax_rate": 0.0,  # Varía por estado, se calcula dinámicamente
        "lang": "pt-br",
        "locale": "pt-BR",
        "timezone": "America/Sao_Paulo",
        "date_format": "DD/MM/YYYY",
        "phone_prefix": "+55",
        "url_prefix": "/br",
        "namespace": "brasil",
    },
    "VE": {
        "currency": "USD",  # Dolarizado de facto, aunque oficialmente VES
        "currency_symbol": "$",
        "decimals": 2,
        "tax_name": "IVA",
        "tax_rate": 16.0,
        "lang": "es",
        "locale": "es-VE",
        "timezone": "America/Caracas",
        "date_format": "DD/MM/YYYY",
        "phone_prefix": "+58",
        "url_prefix": "/ve",
        "namespace": "venezuela",
        # Nota: Venezuela puede requerir moneda_secundaria para conversión VES
        "secondary_currency": "VES",
        "supports_dual_currency": True,
    },
    "AR": {
        "currency": "ARS",
        "currency_symbol": "$",
        "decimals": 2,
        "tax_name": "IVA",
        "tax_rate": 21.0,
        "lang": "es",
        "locale": "es-AR",
        "timezone": "America/Argentina/Buenos_Aires",
        "date_format": "DD/MM/YYYY",
        "phone_prefix": "+54",
        "url_prefix": "/ar",
        "namespace": "argentina",
    },
    "UY": {
        "currency": "UYU",
        "currency_symbol": "$",
        "decimals": 2,
        "tax_name": "IVA",
        "tax_rate": 22.0,
        "lang": "es",
        "locale": "es-UY",
        "timezone": "America/Montevideo",
        "date_format": "DD/MM/YYYY",
        "phone_prefix": "+598",
        "url_prefix": "/uy",
        "namespace": "uruguay",
    },
}

# País por defecto: desde settings (EGARAGE_DEFAULT_COUNTRY) para una sola fuente de verdad
DEFAULT_COUNTRY = getattr(settings, "EGARAGE_DEFAULT_COUNTRY", "cl").upper()


def build_bienvenida_url(country_code, request=None):
    """
    Construye URL de bienvenida con formato /{country}/{lang}/bienvenida/

    El sistema usa URLs con idioma explícito; CountrySettings.build_url no lo incluye.
    Usar SIEMPRE esta función para URLs de bienvenida, nunca build_url con "bienvenida/".

    Args:
        country_code: Código de país (CL, US, MX, etc.)
        request: HttpRequest opcional para URL absoluta

    Returns:
        str: /cl/es/bienvenida/, /us/en/bienvenida/, etc.
    """
    country_code = (country_code or "CL").upper()
    config = get_country_config(country_code)
    lang = config.get("lang", "es")
    if lang == "pt-br":
        lang = "pt"
    path = f"/{country_code.lower()}/{lang}/bienvenida/"
    if request:
        try:
            return request.build_absolute_uri(path)
        except Exception:
            pass
    return path


def get_country_config(country_code):
    """
    Obtiene configuración completa de un país.

    Args:
        country_code: Código ISO 3166-1 alpha-2 del país (ej: 'CL', 'US', 'PE')

    Returns:
        dict: Configuración del país o configuración por defecto (Chile)

    Ejemplo:
        >>> config = get_country_config('PE')
        >>> print(config['currency'])  # 'PEN'
        >>> print(config['decimals'])   # 2
        >>> print(config['tax_rate'])   # 18.0
    """
    if not country_code:
        country_code = DEFAULT_COUNTRY

    country_code = str(country_code).strip().upper()
    return COUNTRY_SETTINGS.get(country_code, COUNTRY_SETTINGS[DEFAULT_COUNTRY])


def get_currency_decimals(country_code):
    """
    Obtiene número de decimales para formateo de moneda.

    Args:
        country_code: Código de país

    Returns:
        int: Número de decimales (0 o 2)
    """
    config = get_country_config(country_code)
    return config["decimals"]


def get_tax_rate(country_code):
    """
    Obtiene tasa de impuesto por defecto para un país.

    Args:
        country_code: Código de país

    Returns:
        float: Tasa de impuesto (ej: 19.0 para 19%)
    """
    config = get_country_config(country_code)
    return config["tax_rate"]


def get_tax_name(country_code):
    """
    Obtiene nombre del impuesto para un país.

    Args:
        country_code: Código de país

    Returns:
        str: Nombre del impuesto (ej: 'IVA', 'IGV', 'Sales Tax')
    """
    config = get_country_config(country_code)
    return config["tax_name"]


def get_currency_symbol(country_code):
    """
    Obtiene símbolo de moneda para un país.

    Args:
        country_code: Código de país

    Returns:
        str: Símbolo de moneda (ej: '$', 'S/', 'R$')
    """
    config = get_country_config(country_code)
    return config["currency_symbol"]


def get_locale(country_code):
    """
    Obtiene locale para formateo de números/fechas.

    Args:
        country_code: Código de país

    Returns:
        str: Locale (ej: 'es-CL', 'en-US', 'pt-BR')
    """
    config = get_country_config(country_code)
    return config["locale"]


def format_currency(amount, country_code, include_symbol=True):
    """
    Formatea un monto según las reglas del país.

    Args:
        amount: Decimal o número a formatear
        country_code: Código de país
        include_symbol: Si incluir símbolo de moneda

    Returns:
        str: Monto formateado (ej: '$1.234', '$1,234.56', 'S/ 1,234.56')

    Ejemplo:
        >>> format_currency(1234.56, 'CL')  # '$1.235'
        >>> format_currency(1234.56, 'US')  # '$1,234.56'
        >>> format_currency(1234.56, 'PE')  # 'S/ 1,234.56'
    """
    from decimal import Decimal, ROUND_HALF_UP

    if amount is None or amount == "":
        amount = Decimal("0")

    if not isinstance(amount, Decimal):
        try:
            amount = Decimal(str(amount))
        except Exception:
            amount = Decimal("0")

    config = get_country_config(country_code)
    decimals = config["decimals"]
    symbol = config["currency_symbol"]

    # Redondear según decimales
    if decimals == 0:
        amount = amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        formatted = f"{amount:,.0f}"
        # Para países sin decimales, usar punto como separador de miles
        formatted = formatted.replace(",", ".")
    else:
        amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        formatted = f"{amount:,.2f}"

    if include_symbol:
        # Agregar espacio después del símbolo si no es $
        if symbol != "$":
            return f"{symbol} {formatted}"
        return f"{symbol}{formatted}"

    return formatted


def get_available_countries():
    """
    Obtiene lista de todos los países disponibles.

    Returns:
        list: Lista de códigos de países
    """
    return list(COUNTRY_SETTINGS.keys())


def is_country_supported(country_code):
    """
    Verifica si un país está soportado.

    Args:
        country_code: Código de país

    Returns:
        bool: True si el país está soportado
    """
    country_code = str(country_code).strip().upper() if country_code else None
    return country_code in COUNTRY_SETTINGS


# Helper para obtener configuración desde una empresa
def get_config_from_empresa(empresa):
    """
    Obtiene configuración de país desde un objeto Empresa.

    Args:
        empresa: Instancia de modelo Empresa

    Returns:
        dict: Configuración del país de la empresa
    """
    if not empresa:
        return get_country_config(DEFAULT_COUNTRY)

    pais = getattr(empresa, "pais", None)
    return get_country_config(pais)


# Helper para obtener configuración desde un documento
def get_config_from_documento(documento):
    """
    Obtiene configuración de país desde un objeto Documento.

    Args:
        documento: Instancia de modelo Documento

    Returns:
        dict: Configuración del país del documento
    """
    if not documento:
        return get_country_config(DEFAULT_COUNTRY)

    # Intentar obtener país del documento directamente
    country = getattr(documento, "country", None)
    if country:
        return get_country_config(country)

    # Si no, obtener de la empresa
    empresa = getattr(documento, "empresa", None)
    return get_config_from_empresa(empresa)
