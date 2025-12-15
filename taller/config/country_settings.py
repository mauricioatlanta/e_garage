"""
Configuración Centralizada de Países y URLs

Elimina hardcoding de URLs y centraliza la configuración de países.
Permite agregar nuevos países fácilmente sin tocar código.
"""

from django.conf import settings


class CountrySettings:
    """
    Configuración centralizada de países y sus propiedades.

    Para agregar un nuevo país, solo agrega una entrada aquí.
    """

    # Configuración completa por país
    COUNTRIES = {
        "CL": {
            "name": "Chile",
            "name_es": "Chile",
            "name_en": "Chile",
            "language": "es",
            "currency": "CLP",
            "currency_symbol": "$",
            "url_prefix": "/cl",
            "url_prefix_legacy": "/es",  # Para canonicalización
            "timezone": "America/Santiago",
            "tax_rate": 19.0,  # IVA 19%
            "tax_label": "IVA",
            "phone_prefix": "+56",
            "date_format": "DD/MM/YYYY",
            "namespace": "chile",
        },
        "US": {
            "name": "United States",
            "name_es": "Estados Unidos",
            "name_en": "United States",
            "language": "en",
            "currency": "USD",
            "currency_symbol": "US$",
            "url_prefix": "/us",
            "url_prefix_legacy": "/en",  # Para canonicalización
            "timezone": "America/New_York",
            "tax_rate": 0.0,  # Sales tax varía por estado
            "tax_label": "Sales Tax",
            "phone_prefix": "+1",
            "date_format": "MM/DD/YYYY",
            "namespace": "usa",
        },
        "MX": {
            "name": "México",
            "name_es": "México",
            "name_en": "Mexico",
            "language": "es",
            "currency": "MXN",
            "currency_symbol": "MX$",
            "url_prefix": "/mx",
            "url_prefix_legacy": None,
            "timezone": "America/Mexico_City",
            "tax_rate": 16.0,  # IVA 16%
            "tax_label": "IVA",
            "phone_prefix": "+52",
            "date_format": "DD/MM/YYYY",
            "namespace": "mexico",
        },
        "PE": {
            "name": "Perú",
            "name_es": "Perú",
            "name_en": "Peru",
            "language": "es",
            "currency": "PEN",
            "currency_symbol": "S/",
            "url_prefix": "/pe",
            "url_prefix_legacy": None,
            "timezone": "America/Lima",
            "tax_rate": 18.0,  # IGV 18%
            "tax_label": "IGV",
            "phone_prefix": "+51",
            "date_format": "DD/MM/YYYY",
            "namespace": "peru",
        },
        "CO": {
            "name": "Colombia",
            "name_es": "Colombia",
            "name_en": "Colombia",
            "language": "es",
            "currency": "COP",
            "currency_symbol": "$",
            "url_prefix": "/co",
            "url_prefix_legacy": None,
            "timezone": "America/Bogota",
            "tax_rate": 19.0,  # IVA 19%
            "tax_label": "IVA",
            "phone_prefix": "+57",
            "date_format": "DD/MM/YYYY",
            "namespace": "colombia",
        },
        "EC": {
            "name": "Ecuador",
            "name_es": "Ecuador",
            "name_en": "Ecuador",
            "language": "es",
            "currency": "USD",  # Ecuador usa dólares
            "currency_symbol": "$",
            "url_prefix": "/ec",
            "url_prefix_legacy": None,
            "timezone": "America/Guayaquil",
            "tax_rate": 12.0,  # IVA 12%
            "tax_label": "IVA",
            "phone_prefix": "+593",
            "date_format": "DD/MM/YYYY",
            "namespace": "ecuador",
        },
        "BR": {
            "name": "Brasil",
            "name_es": "Brasil",
            "name_en": "Brazil",
            "language": "pt-br",
            "currency": "BRL",
            "currency_symbol": "R$",
            "url_prefix": "/br",
            "url_prefix_legacy": None,
            "timezone": "America/Sao_Paulo",
            "tax_rate": 0.0,  # ICMS varía por estado
            "tax_label": "ICMS",
            "phone_prefix": "+55",
            "date_format": "DD/MM/YYYY",
            "namespace": "brasil",
        },
        "VE": {
            "name": "Venezuela",
            "name_es": "Venezuela",
            "name_en": "Venezuela",
            "language": "es",
            "currency": "USD",  # Dolarizado de facto
            "currency_symbol": "$",
            "url_prefix": "/ve",
            "url_prefix_legacy": None,
            "timezone": "America/Caracas",
            "tax_rate": 16.0,  # IVA 16%
            "tax_label": "IVA",
            "phone_prefix": "+58",
            "date_format": "DD/MM/YYYY",
            "namespace": "venezuela",
        },
        "AR": {
            "name": "Argentina",
            "name_es": "Argentina",
            "name_en": "Argentina",
            "language": "es",
            "currency": "ARS",
            "currency_symbol": "$",
            "url_prefix": "/ar",
            "url_prefix_legacy": None,
            "timezone": "America/Argentina/Buenos_Aires",
            "tax_rate": 21.0,  # IVA 21%
            "tax_label": "IVA",
            "phone_prefix": "+54",
            "date_format": "DD/MM/YYYY",
            "namespace": "argentina",
        },
        "UY": {
            "name": "Uruguay",
            "name_es": "Uruguay",
            "name_en": "Uruguay",
            "language": "es",
            "currency": "UYU",
            "currency_symbol": "$",
            "url_prefix": "/uy",
            "url_prefix_legacy": None,
            "timezone": "America/Montevideo",
            "tax_rate": 22.0,  # IVA 22%
            "tax_label": "IVA",
            "phone_prefix": "+598",
            "date_format": "DD/MM/YYYY",
            "namespace": "uruguay",
        },
    }

    # País por defecto
    DEFAULT_COUNTRY = "CL"

    # Mapeo de prefijos legacy a países (para canonicalización)
    LEGACY_PREFIX_TO_COUNTRY = {
        "/es": "CL",
        "/en": "US",
    }

    # Mapeo inverso: país a prefijos legacy
    COUNTRY_TO_LEGACY_PREFIX = {
        "CL": "/es",
        "US": "/en",
    }

    @classmethod
    def get_country_config(cls, country_code):
        """
        Obtiene configuración de un país.

        Args:
            country_code: Código de país ('CL', 'US', 'MX')

        Returns:
            dict: Configuración del país o configuración por defecto
        """
        country_code = (country_code or cls.DEFAULT_COUNTRY).upper()
        return cls.COUNTRIES.get(country_code, cls.COUNTRIES[cls.DEFAULT_COUNTRY])

    @classmethod
    def get_url_prefix(cls, country_code):
        """
        Obtiene prefijo de URL para un país.

        Args:
            country_code: Código de país

        Returns:
            str: Prefijo de URL (ej: '/cl', '/us')
        """
        config = cls.get_country_config(country_code)
        return config.get("url_prefix", f"/{country_code.lower()}")

    @classmethod
    def get_country_from_url(cls, url_path):
        """
        Extrae código de país desde URL.

        Args:
            url_path: Ruta de URL (ej: '/cl/dashboard/', '/us/dashboard/')

        Returns:
            str: Código de país o None
        """
        if not url_path:
            return None

        # Normalizar path
        if not url_path.startswith("/"):
            url_path = "/" + url_path

        # Buscar prefijos canónicos
        for country_code, config in cls.COUNTRIES.items():
            prefix = config.get("url_prefix", "")
            legacy_prefix = config.get("url_prefix_legacy")

            if url_path.startswith(prefix + "/") or url_path == prefix:
                return country_code

            if legacy_prefix and (
                url_path.startswith(legacy_prefix + "/") or url_path == legacy_prefix
            ):
                return country_code

        # Buscar en mapeo legacy
        for legacy_prefix, country_code in cls.LEGACY_PREFIX_TO_COUNTRY.items():
            if url_path.startswith(legacy_prefix + "/") or url_path == legacy_prefix:
                return country_code

        return None

    @classmethod
    def get_available_countries(cls):
        """
        Obtiene lista de países disponibles.

        Returns:
            list: Lista de códigos de países
        """
        return list(cls.COUNTRIES.keys())

    @classmethod
    def build_url(cls, country_code, path="", request=None):
        """
        Construye URL completa con prefijo de país.

        Args:
            country_code: Código de país
            path: Ruta sin prefijo (ej: 'dashboard/', 'documentos/lista/')
            request: HttpRequest (opcional, para URL absoluta)

        Returns:
            str: URL completa
        """
        prefix = cls.get_url_prefix(country_code)

        # Normalizar path
        if path and not path.startswith("/"):
            path = "/" + path
        elif not path:
            path = "/"

        url = prefix + path

        # Construir URL absoluta si hay request
        if request:
            try:
                return request.build_absolute_uri(url)
            except Exception:
                pass

        return url

    @classmethod
    def is_country_valid(cls, country_code):
        """
        Verifica si un código de país es válido.

        Args:
            country_code: Código de país

        Returns:
            bool: True si el país es válido
        """
        return country_code.upper() in cls.COUNTRIES

    @classmethod
    def get_namespace(cls, country_code):
        """
        Obtiene el namespace de URL para un país.

        Args:
            country_code: Código de país

        Returns:
            str: Namespace de URL (ej: 'chile', 'usa')
        """
        config = cls.get_country_config(country_code)
        return config.get("namespace", country_code.lower())

    @classmethod
    def get_available_countries_for_choices(cls):
        """
        Obtiene lista de países en formato para ChoiceField.

        Returns:
            list: Lista de tuplas (código, nombre) para usar en formularios
        """
        choices = []
        for country_code, config in cls.COUNTRIES.items():
            # Usar nombre en español si está disponible, sino nombre en inglés
            name = (
                config.get("name_es") or config.get("name_en") or config.get("name", country_code)
            )
            # Agregar bandera emoji si está disponible
            flag_emoji = {
                "CL": "🇨🇱",
                "US": "🇺🇸",
                "MX": "🇲🇽",
                "PE": "🇵🇪",
                "CO": "🇨🇴",
                "EC": "🇪🇨",
                "BR": "🇧🇷",
                "VE": "🇻🇪",
                "AR": "🇦🇷",
                "UY": "🇺🇾",
            }.get(country_code, "")

            display_name = f"{flag_emoji} {name}" if flag_emoji else name
            choices.append((country_code, display_name))

        return sorted(choices, key=lambda x: x[1])  # Ordenar alfabéticamente por nombre


# Helper functions para uso en código
def get_country_config(country_code):
    """Helper para obtener configuración de país"""
    return CountrySettings.get_country_config(country_code)


def get_url_prefix(country_code):
    """Helper para obtener prefijo de URL"""
    return CountrySettings.get_url_prefix(country_code)


def get_country_from_url(url_path):
    """Helper para extraer país desde URL"""
    return CountrySettings.get_country_from_url(url_path)


def build_country_url(country_code, path="", request=None):
    """Helper para construir URL con prefijo de país"""
    return CountrySettings.build_url(country_code, path, request)


def is_country_valid(country_code):
    """Helper para verificar si país es válido"""
    return CountrySettings.is_country_valid(country_code)
