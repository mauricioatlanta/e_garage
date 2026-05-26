from django.conf import settings

from taller.utils.email_helper import get_support_reply_to
from taller.utils.plan_catalog import (
    BILLING_ANNUAL,
    BILLING_MONTHLY,
    DEFAULT_PAYMENT_METHODS,
    LEGACY_BILLING_MAPPING,
    LEGACY_PLAN_MAPPING,
    PAYMENT_METHOD_BANK_TRANSFER,
    PAYMENT_METHOD_FLOW,
    PAYMENT_METHOD_MERCADOPAGO,
    PAYMENT_METHOD_PAYPAL,
    PLAN_BUSINESS,
    PLAN_ENTRY,
    PLAN_GROWTH,
    PLAN_TRIAL,
    get_plan_price,
    get_plan_display_name,
    get_supported_payment_methods,
    normalize_billing_cycle,
    normalize_legacy_billing,
    normalize_legacy_plan,
    normalize_plan_code,
)


def normalize_company_plan(plan_code):
    """Mapea códigos legacy y actuales a los planes modernos de Empresa."""
    return normalize_plan_code(plan_code)


def normalize_billing_cycle_value(billing_cycle):
    """Normaliza ciclos legacy y actuales a monthly/anual."""
    return normalize_billing_cycle(billing_cycle)


def get_supported_payment_methods_for_country(country="CL"):
    return get_supported_payment_methods(country)


def get_plan_price_for_country(country, plan_code, billing_cycle):
    return get_plan_price(country, plan_code, billing_cycle)


def get_plan_display_name_for_locale(plan_code, lang="en"):
    return get_plan_display_name(plan_code, lang=lang)


def _setting(name, default=""):
    value = getattr(settings, name, default)
    if isinstance(value, str):
        return value.strip()
    return value


def get_transfer_payment_details(country="CL"):
    country = (country or "CL").strip().upper()

    defaults = {
        "CL": {
            "banco": "Banco Estado",
            "tipo_cuenta": "Chequera Electrónica (Cuenta Vista)",
            "titular": "ATLANTA RECICLAJES SPA",
            "rut": "77.350.892-5",
            "numero_cuenta": "23572156761",
            "email_confirmacion": get_support_reply_to(),
            "tax_id_label": "RUT",
            "account_number_label": "Número de cuenta",
        },
        "MX": {
            "banco": "BBVA Mexico",
            "tipo_cuenta": "Cuenta CLABE",
            "titular": _setting("SITE_NAME", "eGarage") or "eGarage",
            "rut": "",
            "numero_cuenta": "",
            "email_confirmacion": get_support_reply_to(),
            "tax_id_label": "RFC",
            "account_number_label": "CLABE",
        },
        "US": {
            "banco": "Bank transfer",
            "tipo_cuenta": "Business account",
            "titular": _setting("SITE_NAME", "eGarage") or "eGarage",
            "rut": "",
            "numero_cuenta": "",
            "email_confirmacion": get_support_reply_to(),
            "tax_id_label": "Tax ID",
            "account_number_label": "Account",
        },
    }

    key = country if country in defaults else "CL"
    data = defaults[key].copy()
    prefix = f"SUBSCRIPTION_{key}_"

    data["banco"] = _setting(f"{prefix}BANK_NAME", data["banco"])
    data["tipo_cuenta"] = _setting(f"{prefix}ACCOUNT_TYPE", data["tipo_cuenta"])
    data["titular"] = _setting(f"{prefix}ACCOUNT_HOLDER", data["titular"])
    data["rut"] = _setting(f"{prefix}TAX_ID", data["rut"])
    data["numero_cuenta"] = _setting(f"{prefix}ACCOUNT_NUMBER", data["numero_cuenta"])
    data["email_confirmacion"] = _setting(
        f"{prefix}CONFIRMATION_EMAIL", data["email_confirmacion"]
    ) or get_support_reply_to()

    return data


def build_transfer_payment_message(country="CL"):
    details = get_transfer_payment_details(country)
    return (
        f"Banco: {details['banco']}\n"
        f"Tipo de cuenta: {details['tipo_cuenta']}\n"
        f"Titular: {details['titular']}\n"
        f"{details['tax_id_label']}: {details['rut'] or 'Por confirmar'}\n"
        f"{details['account_number_label']}: {details['numero_cuenta'] or 'Por confirmar'}\n"
        f"Correo para enviar voucher: {details['email_confirmacion']}"
    )


def get_paypal_business_email():
    return _setting("PAYPAL_BUSINESS_EMAIL", "") or get_support_reply_to()
