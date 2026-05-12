import requests

from django.conf import settings


class MPAPIError(Exception):
    """Error controlado para Mercado Pago."""


def _setting(name, default=""):
    value = getattr(settings, name, default)
    if isinstance(value, str):
        return value.strip()
    return value


def _get_required_setting(name):
    value = _setting(name, "")
    if not value:
        raise MPAPIError(f"Configuracion incompleta de Mercado Pago: falta {name}")
    return value


def _get_timeout_seconds():
    timeout = _setting("MP_TIMEOUT", 15)
    try:
        return int(timeout)
    except (TypeError, ValueError):
        return 15


def _authorization_headers():
    return {
        "Authorization": f"Bearer {_get_required_setting('MP_ACCESS_TOKEN')}",
        "Content-Type": "application/json",
    }


def create_mp_preference(transaccion, *, success_url=None, failure_url=None, pending_url=None, webhook_url=None, session=None):
    """Crea una preferencia de Checkout Pro y persiste el id de la preferencia."""
    api_url = "https://api.mercadopago.com/checkout/preferences"
    success_url = success_url or _get_required_setting("MP_URL_SUCCESS")
    failure_url = failure_url or _get_required_setting("MP_URL_FAILURE")
    pending_url = pending_url or _get_required_setting("MP_URL_PENDING")
    webhook_url = webhook_url or _get_required_setting("MP_URL_WEBHOOK")

    preference_data = {
        "items": [
            {
                "title": transaccion.description or f"Suscripcion eGarage - {transaccion.get_billing_cycle_display()}",
                "quantity": 1,
                "currency_id": transaccion.currency,
                "unit_price": float(transaccion.amount),
            }
        ],
        "external_reference": str(transaccion.id),
        "back_urls": {
            "success": success_url,
            "failure": failure_url,
            "pending": pending_url,
        },
        "auto_return": "approved",
        "notification_url": webhook_url,
    }

    client = session or requests
    response = client.post(
        api_url,
        json=preference_data,
        headers=_authorization_headers(),
        timeout=_get_timeout_seconds(),
    )
    if response.status_code not in {200, 201}:
        raise MPAPIError(f"Mercado Pago devolvio HTTP {response.status_code}: {response.text}")

    data = response.json()
    preference_id = data.get("id")
    init_point = data.get("init_point")
    if not preference_id or not init_point:
        raise MPAPIError("Mercado Pago no devolvio id o init_point")

    gateway_payload = dict(transaccion.gateway_payload or {})
    gateway_payload["mp_preference_response"] = data
    transaccion.external_transaction_id = str(preference_id)
    transaccion.checkout_url = init_point
    transaccion.gateway_payload = gateway_payload
    transaccion.save(
        update_fields=[
            "external_transaction_id",
            "checkout_url",
            "gateway_payload",
            "updated_at",
        ]
    )
    return init_point


def get_mp_payment(payment_id, *, session=None):
    """Obtiene el estado completo de un pago en Mercado Pago."""
    payment_id = str(payment_id).strip()
    if not payment_id:
        raise MPAPIError("Falta payment_id para consultar Mercado Pago")

    client = session or requests
    response = client.get(
        f"https://api.mercadopago.com/v1/payments/{payment_id}",
        headers=_authorization_headers(),
        timeout=_get_timeout_seconds(),
    )
    if response.status_code != 200:
        raise MPAPIError(f"Mercado Pago devolvio HTTP {response.status_code}: {response.text}")
    return response.json()
