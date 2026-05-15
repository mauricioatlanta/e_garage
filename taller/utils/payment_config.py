from django.conf import settings

from taller.utils.email_helper import get_support_reply_to


BILLING_CYCLE_TO_PLAN = {
    "mensual": "basic",
    "semestral": "premium",
    "anual": "enterprise",
}


def normalize_company_plan(plan_code):
    """Mapea ciclos de cobro legacy a los planes vigentes de Empresa."""
    if not plan_code:
        return "trial"
    return BILLING_CYCLE_TO_PLAN.get(str(plan_code).strip().lower(), plan_code)


def _setting(name, default=""):
    value = getattr(settings, name, default)
    if isinstance(value, str):
        return value.strip()
    return value


def get_transfer_payment_details(country="CL"):
    country = (country or "CL").strip().upper()

    defaults = {
        "CL": {
            "banco": "BancoEstado",
            "tipo_cuenta": "Cuenta Corriente",
            "titular": _setting("SITE_NAME", "eGarage") or "eGarage",
            "rut": "",
            "numero_cuenta": "",
            "email_confirmacion": get_support_reply_to(),
            "tax_id_label": "RUT",
            "account_number_label": "Numero de cuenta",
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
