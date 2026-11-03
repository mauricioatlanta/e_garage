#billing_countries.py
ALLOWED_COUNTRIES = {
    "CL": {"name": "Chile", "currency": "USD", "primary_gateway": "paypal", "supports_usd_recurrent": True, "tax_applies": True},
    "PE": {"name": "Peru", "currency": "USD", "primary_gateway": "paypal", "supports_usd_recurrent": True, "tax_applies": False},
    "UY": {"name": "Uruguay", "currency": "USD", "primary_gateway": "paypal", "supports_usd_recurrent": True, "tax_applies": False},
    "PY": {"name": "Paraguay", "currency": "USD", "primary_gateway": "paypal", "supports_usd_recurrent": True, "tax_applies": False},
    "CO": {"name": "Colombia", "currency": "USD", "primary_gateway": "paypal", "supports_usd_recurrent": True, "tax_applies": False},
    "EC": {"name": "Ecuador", "currency": "USD", "primary_gateway": "paypal", "supports_usd_recurrent": True, "tax_applies": False},
    "US": {"name": "Estados Unidos", "currency": "USD", "primary_gateway": "paypal", "supports_usd_recurrent": True, "tax_applies": False},
    "MX": {"name": "Mexico", "currency": "USD", "primary_gateway": "paypal", "supports_usd_recurrent": True, "tax_applies": False},
    "BR": {"name": "Brasil", "currency": "USD", "primary_gateway": "paypal", "supports_usd_recurrent": True, "tax_applies": False},
    "CR": {"name": "Costa Rica", "currency": "USD", "primary_gateway": "paypal", "supports_usd_recurrent": True, "tax_applies": False},
    "PA": {"name": "Panama", "currency": "USD", "primary_gateway": "paypal", "supports_usd_recurrent": True, "tax_applies": False},
    "DO": {"name": "Republica Dominicana", "currency": "USD", "primary_gateway": "paypal", "supports_usd_recurrent": True, "tax_applies": False},
}

RESTRICTED_COUNTRIES = {
    "CU": {"name": "Cuba", "reason": "Sanciones internacionales / Bloqueo pasarelas"},
    "VE": {"name": "Venezuela", "reason": "Restricciones cambiarias / Falta liquidacion recurrente"},
    "NI": {"name": "Nicaragua", "reason": "Restricciones regulatorias"},
    "RU": {"name": "Rusia", "reason": "Sanciones financieras internacionales"},
    "BY": {"name": "Bielorrusia", "reason": "Sanciones financieras internacionales"},
    "IR": {"name": "Iran", "reason": "Sanciones OFAC"},
    "SY": {"name": "Siria", "reason": "Sanciones OFAC"},
    "KP": {"name": "Corea del Norte", "reason": "Sanciones OFAC"},
    "AR": {"name": "Argentina", "reason": "Control cambiario e impuestos a divisas"},
    "BO": {"name": "Bolivia", "reason": "Restriccion de acceso a divisas USD"},
}


def validate_signup_country(country_code: str) -> dict:
    code = (country_code or "").strip().upper()
    if code in ALLOWED_COUNTRIES:
        cfg = ALLOWED_COUNTRIES[code]
        return {
            "allowed": True,
            "country_code": code,
            "country_name": cfg["name"],
            "gateway": cfg["primary_gateway"],
            "supports_usd": cfg["supports_usd_recurrent"],
            "message": "Pais habilitado.",
        }
    if code in RESTRICTED_COUNTRIES:
        blk = RESTRICTED_COUNTRIES[code]
        return {
            "allowed": False,
            "country_code": code,
            "country_name": blk["name"],
            "reason": blk["reason"],
            "message": f"Servicio no disponible en {blk['name']}: {blk['reason']}.",
        }
    return {
        "allowed": False,
        "country_code": code,
        "country_name": "Desconocido",
        "reason": "Fuera de cobertura",
        "message": "Region fuera de cobertura.",
    }
