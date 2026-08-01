from __future__ import annotations

from datetime import datetime, timedelta, timezone

from transbank.common.integration_type import IntegrationType
from transbank.common.options import WebpayOptions
from transbank.webpay.webpay_plus.transaction import Transaction

from .gateway import PaymentConfirmation, PaymentGateway, PaymentInitiation

_SANDBOX_COMMERCE_CODE = "597055555532"
_SANDBOX_API_KEY = (
    "579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C"
)


class WebPayGateway(PaymentGateway, key="webpay"):
    def __init__(
        self,
        commerce_code: str,
        api_key: str,
        integration_type: IntegrationType,
    ) -> None:
        self._options = WebpayOptions(
            commerce_code=commerce_code,
            api_key=api_key,
            integration_type=integration_type,
        )

    @classmethod
    def from_settings(cls) -> WebPayGateway:
        from django.conf import settings

        commerce_code = getattr(settings, "TBK_COMMERCE_CODE", _SANDBOX_COMMERCE_CODE)
        api_key = getattr(settings, "TBK_API_KEY", _SANDBOX_API_KEY)
        integration_type = (
            IntegrationType.LIVE
            if getattr(settings, "TBK_PRODUCTION", False)
            else IntegrationType.TEST
        )
        return cls(
            commerce_code=commerce_code,
            api_key=api_key,
            integration_type=integration_type,
        )

    def initiate(
        self, buy_order: str, session_id: str, amount: int, return_url: str
    ) -> PaymentInitiation:
        tx = Transaction(self._options)
        r = tx.create(
            buy_order=buy_order,
            session_id=session_id,
            amount=amount,
            return_url=return_url,
        )
        return PaymentInitiation(
            redirect_url=f"{r.url}?token_ws={r.token}",
            gateway_token=r.token,
            expires_at=datetime.now(tz=timezone.utc) + timedelta(minutes=5),
        )

    def confirm(self, gateway_token: str) -> PaymentConfirmation:
        tx = Transaction(self._options)
        r = tx.commit(gateway_token)

        card_number = ""
        if getattr(r, "card_detail", None):
            card_number = getattr(r.card_detail, "card_number", "") or ""
        card_last4 = card_number[-4:] if len(card_number) >= 4 else ""

        success = getattr(r, "response_code", -1) == 0
        raw = {
            "response_code": getattr(r, "response_code", None),
            "authorization_code": getattr(r, "authorization_code", None),
            "amount": float(getattr(r, "amount", 0) or 0),
            "status": getattr(r, "status", None),
            "buy_order": getattr(r, "buy_order", None),
            "session_id": getattr(r, "session_id", None),
            "payment_type_code": getattr(r, "payment_type_code", None),
            "card_number": card_number,
        }
        return PaymentConfirmation(
            success=success,
            gateway_ref=raw.get("authorization_code") or "",
            authorization_code=raw.get("authorization_code") or "",
            card_last4=card_last4,
            amount=int(raw["amount"]),
            raw_response=raw,
        )
