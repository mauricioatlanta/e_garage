import hashlib
import hmac
from decimal import Decimal

import requests

from django.conf import settings


class FlowAPIError(Exception):
    """Error controlado para respuestas invalidas o configuracion incompleta de Flow."""


def _setting(name, default=""):
    value = getattr(settings, name, default)
    if isinstance(value, str):
        return value.strip()
    return value


def _get_required_setting(name):
    value = _setting(name, "")
    if not value:
        raise FlowAPIError(f"Configuracion incompleta de Flow: falta {name}")
    return value


def _normalize_signature_value(value):
    if isinstance(value, Decimal):
        return int(value)
    return value


def get_flow_signature(params):
    """Genera la firma HMAC-SHA256 requerida por Flow."""
    signable = {
        key: _normalize_signature_value(value)
        for key, value in params.items()
        if key != "s" and value not in (None, "")
    }
    pieces = []
    for key in sorted(signable.keys()):
        pieces.append(f"{key}{signable[key]}")
    to_sign = "".join(pieces)
    secret_key = _get_required_setting("FLOW_SECRET_KEY")
    return hmac.new(secret_key.encode(), to_sign.encode(), hashlib.sha256).hexdigest()


def _get_flow_api_url():
    return _get_required_setting("FLOW_API_URL").rstrip("/")


def _get_timeout_seconds():
    timeout = _setting("FLOW_TIMEOUT", 15)
    try:
        return int(timeout)
    except (TypeError, ValueError):
        return 15


def create_payment_order(transaccion, *, return_url=None, confirmation_url=None, session=None):
    """Crea una orden en Flow y persiste el token/checkout en SuscripcionTransaccion."""
    api_url = _get_flow_api_url()
    api_key = _get_required_setting("FLOW_API_KEY")
    customer_email = transaccion.customer_email or getattr(transaccion.empresa, "email", "")
    if not customer_email:
        customer_email = getattr(getattr(transaccion.empresa, "user", None), "email", "")
    if not customer_email:
        raise FlowAPIError("La empresa no tiene email de contacto para crear la orden en Flow")

    flow_return_url = return_url or _get_required_setting("FLOW_URL_RETURN")
    flow_confirmation_url = confirmation_url or _get_required_setting("FLOW_URL_CONFIRMATION")
    commerce_order = transaccion.reference or f"SUB-{transaccion.uuid.hex}"

    params = {
        "apiKey": api_key,
        "commerceOrder": commerce_order,
        "subject": transaccion.description or f"Suscripcion eGarage - {transaccion.get_billing_cycle_display()}",
        "currency": transaccion.currency,
        "amount": int(transaccion.amount),
        "email": customer_email,
        "urlConfirmation": flow_confirmation_url,
        "urlReturn": flow_return_url,
    }
    params["s"] = get_flow_signature(params)

    client = session or requests
    response = client.post(
        f"{api_url}/payment/create",
        data=params,
        timeout=_get_timeout_seconds(),
    )
    if response.status_code != 200:
        raise FlowAPIError(f"Flow devolvio HTTP {response.status_code}: {response.text}")

    data = response.json()
    token = data.get("token")
    checkout_base_url = data.get("url")
    if not token or not checkout_base_url:
        raise FlowAPIError("Flow no devolvio token o url de checkout")

    gateway_payload = dict(transaccion.gateway_payload or {})
    gateway_payload["flow_create_response"] = data

    transaccion.reference = commerce_order
    transaccion.external_transaction_id = token
    transaccion.checkout_url = f"{checkout_base_url}?token={token}"
    transaccion.gateway_payload = gateway_payload
    transaccion.save(
        update_fields=[
            "reference",
            "external_transaction_id",
            "checkout_url",
            "gateway_payload",
            "updated_at",
        ]
    )
    return transaccion.checkout_url


def get_payment_status(token, *, session=None):
    """Consulta el estado de una transaccion de Flow usando payment/getStatus."""
    api_url = _get_flow_api_url()
    params = {
        "apiKey": _get_required_setting("FLOW_API_KEY"),
        "token": token,
    }
    params["s"] = get_flow_signature(params)

    client = session or requests
    response = client.get(
        f"{api_url}/payment/getStatus",
        params=params,
        timeout=_get_timeout_seconds(),
    )
    if response.status_code != 200:
        raise FlowAPIError(f"Flow devolvio HTTP {response.status_code}: {response.text}")
    return response.json()
