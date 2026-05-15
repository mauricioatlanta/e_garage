"""
Servicio de configuración por país para eGarage
"""


def get_country_config(country_code):
    """
    Retorna la configuración para un país específico
    """
    configs = {
        "CL": {
            "lang": "es",
            "currency": "CLP",
            "name": "Chile",
            "tax_label": "IVA",
            "tax_rate": 19.00,
            "symbol": "$",
        },
        "US": {
            "lang": "en",
            "currency": "USD",
            "name": "United States",
            "tax_label": "Sales Tax",
            "tax_rate": 0.00,  # Configurable por estado
            "symbol": "$",
        },
        "PE": {
            "lang": "es",
            "currency": "PEN",
            "name": "Perú",
            "tax_label": "IGV",
            "tax_rate": 18.00,
            "symbol": "S/",
        },
        "BR": {
            "lang": "pt",
            "currency": "BRL",
            "name": "Brasil",
            "tax_label": "IPI/ICMS",
            "tax_rate": 0.00,
            "symbol": "R$",
        },
        "CO": {
            "lang": "es",
            "currency": "COP",
            "name": "Colombia",
            "tax_label": "IVA",
            "tax_rate": 19.00,
            "symbol": "$",
        },
        "EC": {
            "lang": "es",
            "currency": "USD",
            "name": "Ecuador",
            "tax_label": "IVA",
            "tax_rate": 12.00,
            "symbol": "$",
        },
        "VE": {
            "lang": "es",
            "currency": "VES",
            "name": "Venezuela",
            "tax_label": "IVA",
            "tax_rate": 16.00,
            "symbol": "Bs.",
        },
        "MX": {
            "lang": "es",
            "currency": "MXN",
            "name": "México",
            "tax_label": "IVA",
            "tax_rate": 16.00,
            "symbol": "$",
        },
        "UY": {
            "lang": "es",
            "currency": "UYU",
            "name": "Uruguay",
            "tax_label": "IVA",
            "tax_rate": 22.00,
            "symbol": "$",
        },
        "AR": {
            "lang": "es",
            "currency": "ARS",
            "name": "Argentina",
            "tax_label": "IVA",
            "tax_rate": 21.00,
            "symbol": "$",
        },
    }

    return configs.get(
        country_code.upper(),
        {
            "lang": "es",
            "currency": "USD",
            "name": "Unknown",
            "tax_label": "Tax",
            "tax_rate": 0.00,
            "symbol": "$",
        },
    )
