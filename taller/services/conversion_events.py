from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

SIGNUP_STARTED = "signup_started"
SIGNUP_COMPLETED = "signup_completed"
TRIAL_ACTIVATED = "trial_activated"
PAYMENT_SUCCESS = "payment_success"
PAYMENT_FAILED = "payment_failed"
RENEWAL_SUCCESS = "renewal_success"
CHURN = "churn"

CONVERSION_EVENT_NAMES = frozenset(
    {
        SIGNUP_STARTED,
        SIGNUP_COMPLETED,
        TRIAL_ACTIVATED,
        PAYMENT_SUCCESS,
        PAYMENT_FAILED,
        RENEWAL_SUCCESS,
        CHURN,
    }
)


@dataclass(frozen=True)
class ConversionEvent:
    name: str
    user_id: int | None = None
    empresa_id: int | None = None
    country: str = ""
    plan: str = ""
    billing_cycle: str = ""
    amount: str = ""
    currency: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def build_conversion_event(name: str, **kwargs: Any) -> ConversionEvent:
    if name not in CONVERSION_EVENT_NAMES:
        logger.warning("Unknown conversion event name: %s", name)
    return ConversionEvent(name=name, **kwargs)


def track_conversion_event(name: str, **kwargs: Any) -> ConversionEvent:
    event = build_conversion_event(name, **kwargs)
    logger.info(
        "conversion_event",
        extra={
            "conversion_event": {
                "name": event.name,
                "user_id": event.user_id,
                "empresa_id": event.empresa_id,
                "country": event.country,
                "plan": event.plan,
                "billing_cycle": event.billing_cycle,
                "amount": event.amount,
                "currency": event.currency,
                "metadata": event.metadata,
            }
        },
    )
    return event
