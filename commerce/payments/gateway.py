from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class PaymentInitiation:
    redirect_url: str
    gateway_token: str
    expires_at: datetime


@dataclass(frozen=True)
class PaymentConfirmation:
    success: bool
    gateway_ref: str
    authorization_code: str
    card_last4: str
    amount: int
    raw_response: dict


class PaymentGateway(ABC):
    _registry: dict[str, type[PaymentGateway]] = {}

    def __init_subclass__(cls, key: str = "", **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if key:
            PaymentGateway._registry[key] = cls

    @classmethod
    def resolve(cls, key: str) -> PaymentGateway:
        if key not in cls._registry:
            raise KeyError(
                f"Gateway '{key}' no registrado. Disponibles: {list(cls._registry)}"
            )
        return cls._registry[key].from_settings()

    @classmethod
    def from_settings(cls) -> PaymentGateway:
        raise NotImplementedError

    @abstractmethod
    def initiate(
        self, buy_order: str, session_id: str, amount: int, return_url: str
    ) -> PaymentInitiation: ...

    @abstractmethod
    def confirm(self, gateway_token: str) -> PaymentConfirmation: ...
