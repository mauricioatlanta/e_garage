from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from .gateway import PaymentConfirmation, PaymentGateway, PaymentInitiation


class BankTransferGateway(PaymentGateway, key="bank_transfer"):
    """
    Gateway para transferencia bancaria manual.

    initiate() genera un token local y devuelve la URL de instrucciones.
    confirm() siempre lanza NotImplementedError: la verificación es manual,
    delegada a CommercePaymentService.verify_bank_transfer() (H2).
    """

    @classmethod
    def from_settings(cls) -> BankTransferGateway:
        return cls()

    def initiate(
        self, buy_order: str, session_id: str, amount: int, return_url: str
    ) -> PaymentInitiation:
        token = f"bt_{uuid.uuid4().hex}"
        return PaymentInitiation(
            redirect_url=f"/commerce/checkout/bank-transfer/{token}/",
            gateway_token=token,
            expires_at=datetime.now(tz=timezone.utc) + timedelta(days=3),
        )

    def confirm(self, gateway_token: str) -> PaymentConfirmation:
        raise NotImplementedError(
            "BankTransfer requiere verificación manual. "
            "Usar CommercePaymentService.verify_bank_transfer() (H2)."
        )
