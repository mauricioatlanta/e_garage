"""
Feature flags y defaults por país (comportamiento por defecto del país).
No reemplaza config de empresa ni tax engine por ciudad/estado.
"""

COUNTRY_FEATURES = {
    "CL": {
        "allowed_languages": ["es"],
        "default_language": "es",
        "tax_mode": "iva",
        "tax_label": "IVA",
        "tax_default_rate": 19.0,
        "apply_tax_to_parts": True,
        "apply_tax_to_services": False,
        "apply_tax_to_others": False,
        "currency_code": "CLP",
        "currency_symbol": "$",
        "tax_id_label": "RUT",
        "tax_id_type_default": "CL_RUT",
        "tax_id_required": False,
        "mileage_unit": "km",
        "show_patente_as_primary": True,
        "show_vin_as_primary": False,
        "electronic_invoice": True,
        "export_sii": True,
        "url_has_language_prefix": True,
    },
    "US": {
        "allowed_languages": ["en", "es"],
        "default_language": "en",
        "tax_mode": "sales_tax",
        "tax_label": "Sales Tax",
        "tax_default_rate": 0.0,
        "apply_tax_to_parts": True,
        "apply_tax_to_services": False,
        "apply_tax_to_others": False,
        "currency_code": "USD",
        "currency_symbol": "$",
        "tax_id_label": "EIN",
        "tax_id_type_default": "US_EIN",
        "tax_id_required": False,
        "mileage_unit": "mi",
        "show_patente_as_primary": False,
        "show_vin_as_primary": True,
        "electronic_invoice": False,
        "export_sii": False,
        "url_has_language_prefix": True,
    },
}
