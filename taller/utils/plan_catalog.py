from __future__ import annotations

from decimal import Decimal
from typing import Any

PLAN_TRIAL = "trial"
PLAN_ENTRY = "entry"
PLAN_GROWTH = "growth"
PLAN_BUSINESS = "business"

BILLING_MONTHLY = "monthly"
BILLING_ANNUAL = "annual"

LEGACY_PLAN_MAPPING = {
    "basic": PLAN_ENTRY,
    "premium": PLAN_GROWTH,
    "enterprise": PLAN_BUSINESS,
}

LEGACY_BILLING_MAPPING = {
    "mensual": (PLAN_ENTRY, BILLING_MONTHLY),
    "semestral": (PLAN_GROWTH, BILLING_ANNUAL),
    "anual": (PLAN_BUSINESS, BILLING_ANNUAL),
}

LEGACY_PLAN_BILLING_MAPPING = {
    "basic": BILLING_MONTHLY,
    "premium": BILLING_ANNUAL,
    "enterprise": BILLING_ANNUAL,
}

PAYMENT_METHOD_FLOW = "flow"
PAYMENT_METHOD_PAYPAL = "paypal"
PAYMENT_METHOD_MERCADOPAGO = "mercadopago"
PAYMENT_METHOD_BANK_TRANSFER = "bank_transfer"

SUPPORTED_PAYMENT_METHODS_BY_COUNTRY = {
    "CL": [PAYMENT_METHOD_FLOW, PAYMENT_METHOD_BANK_TRANSFER],
    "MX": [PAYMENT_METHOD_MERCADOPAGO, PAYMENT_METHOD_PAYPAL, PAYMENT_METHOD_BANK_TRANSFER],
    "US": [PAYMENT_METHOD_PAYPAL, PAYMENT_METHOD_BANK_TRANSFER],
}
DEFAULT_PAYMENT_METHODS = [PAYMENT_METHOD_PAYPAL, PAYMENT_METHOD_BANK_TRANSFER]

PLAN_LIMITS = {
    PLAN_TRIAL:    {"users_min": 1, "users_max": 1},
    PLAN_ENTRY:    {"users_min": 1, "users_max": 1},
    PLAN_GROWTH:   {"users_min": 2, "users_max": 4},
    PLAN_BUSINESS: {"users_min": 5, "users_max": 10},
    # Aliases de negocio (Express / Taller / Pro)
    "express": {"users_min": 1, "users_max": 1},
    "taller":  {"users_min": 2, "users_max": 4},
    "pro":     {"users_min": 5, "users_max": 10},
}

PLAN_DISPLAY_NAMES = {
    "en": {
        PLAN_TRIAL: "Trial",
        PLAN_ENTRY: "Express",
        PLAN_GROWTH: "Taller",
        PLAN_BUSINESS: "Pro",
        "express": "Express",
        "taller": "Taller",
        "pro": "Pro",
    },
    "es": {
        PLAN_TRIAL: "Trial",
        PLAN_ENTRY: "Express",
        PLAN_GROWTH: "Taller",
        PLAN_BUSINESS: "Pro",
        "express": "Express",
        "taller": "Taller",
        "pro": "Pro",
    },
}

PLAN_DESCRIPTIONS = {
    "en": {
        PLAN_TRIAL: "30 days free",
        PLAN_ENTRY: "1 user — best for solo workshops",
        PLAN_GROWTH: "Up to 4 users — great for small teams",
        PLAN_BUSINESS: "Up to 10 users — designed for growing businesses",
        "express": "1 user — best for solo workshops",
        "taller": "Up to 4 users — great for small teams",
        "pro": "Up to 10 users — designed for growing businesses",
    },
    "es": {
        PLAN_TRIAL: "30 días gratis",
        PLAN_ENTRY: "1 usuario — ideal para un solo operador",
        PLAN_GROWTH: "Hasta 4 usuarios — perfecto para equipos pequeños",
        PLAN_BUSINESS: "Hasta 10 usuarios — para talleres en crecimiento",
        "express": "1 usuario — ideal para un solo operador",
        "taller": "Hasta 4 usuarios — perfecto para equipos pequeños",
        "pro": "Hasta 10 usuarios — para talleres en crecimiento",
    },
}

PRICE_MATRIX = {
    "CL": {
        PLAN_ENTRY: {BILLING_MONTHLY: Decimal("20000"), BILLING_ANNUAL: Decimal("200000")},
        PLAN_GROWTH: {BILLING_MONTHLY: Decimal("39000"), BILLING_ANNUAL: Decimal("390000")},
        PLAN_BUSINESS: {BILLING_MONTHLY: Decimal("69000"), BILLING_ANNUAL: Decimal("690000")},
    },
    "US": {
        PLAN_ENTRY: {BILLING_MONTHLY: Decimal("20"), BILLING_ANNUAL: Decimal("200")},
        PLAN_GROWTH: {BILLING_MONTHLY: Decimal("39"), BILLING_ANNUAL: Decimal("390")},
        PLAN_BUSINESS: {BILLING_MONTHLY: Decimal("69"), BILLING_ANNUAL: Decimal("690")},
    },
    "MX": {
        PLAN_ENTRY: {BILLING_MONTHLY: Decimal("399"), BILLING_ANNUAL: Decimal("3990")},
        PLAN_GROWTH: {BILLING_MONTHLY: Decimal("399"), BILLING_ANNUAL: Decimal("2199")},
        PLAN_BUSINESS: {BILLING_MONTHLY: Decimal("399"), BILLING_ANNUAL: Decimal("3990")},
    },
}

DEFAULT_COUNTRY = "US"
DEFAULT_CURRENCY = "USD"
COUNTRY_CURRENCY = {
    "CL": "CLP",
    "US": "USD",
    "MX": "MXN",
}

MONTHS_BY_BILLING_CYCLE = {
    BILLING_MONTHLY: 1,
    BILLING_ANNUAL: 12,
}

ALL_PLAN_CODES = {PLAN_TRIAL, PLAN_ENTRY, PLAN_GROWTH, PLAN_BUSINESS}
ALL_BILLING_PERIODS = {BILLING_MONTHLY, BILLING_ANNUAL}


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def normalize_plan_code(plan_code: Any) -> str:
    normalized = _normalize_text(plan_code)
    if not normalized:
        return PLAN_TRIAL

    if normalized in ALL_PLAN_CODES:
        return normalized

    if normalized in LEGACY_PLAN_MAPPING:
        return LEGACY_PLAN_MAPPING[normalized]

    if normalized in LEGACY_BILLING_MAPPING:
        return LEGACY_BILLING_MAPPING[normalized][0]

    # Fall back to trial for unknown values to avoid breaking flows
    return PLAN_TRIAL


def normalize_billing_cycle(billing_cycle: Any) -> str:
    normalized = _normalize_text(billing_cycle)
    if not normalized:
        return BILLING_MONTHLY

    if normalized in {BILLING_MONTHLY, BILLING_ANNUAL}:
        return normalized

    if normalized in {PLAN_ENTRY, PLAN_GROWTH, PLAN_BUSINESS}:
        if normalized == PLAN_ENTRY:
            return BILLING_MONTHLY
        return BILLING_ANNUAL

    if normalized == "mensual" or normalized == "basic":
        return BILLING_MONTHLY
    if normalized == "semestral" or normalized == "premium":
        return BILLING_ANNUAL
    if normalized == "anual" or normalized == "enterprise":
        return BILLING_ANNUAL

    return BILLING_MONTHLY


def normalize_legacy_plan(plan_code: Any) -> str:
    normalized = _normalize_text(plan_code)
    if normalized in ALL_PLAN_CODES:
        return normalized
    return LEGACY_PLAN_MAPPING.get(normalized, PLAN_TRIAL)


def normalize_legacy_billing(billing_cycle: Any) -> tuple[str, str]:
    normalized = _normalize_text(billing_cycle)
    if normalized in LEGACY_BILLING_MAPPING:
        return LEGACY_BILLING_MAPPING[normalized]
    return (PLAN_ENTRY, BILLING_MONTHLY)


def get_plan_limits(plan_code: Any) -> dict[str, int]:
    plan = normalize_plan_code(plan_code)
    return PLAN_LIMITS.get(plan, {"users_min": 1, "users_max": 1})


def get_plan_display_name(plan_code: Any, lang: str = "en") -> str:
    plan = normalize_plan_code(plan_code)
    return PLAN_DISPLAY_NAMES.get(lang, PLAN_DISPLAY_NAMES["en"]).get(plan, plan.title())


def get_plan_description(plan_code: Any, lang: str = "en") -> str:
    plan = normalize_plan_code(plan_code)
    return PLAN_DESCRIPTIONS.get(lang, PLAN_DESCRIPTIONS["en"]).get(plan, "")


def get_supported_payment_methods(country_code: Any) -> list[str]:
    country = _normalize_text(country_code).upper()
    if not country:
        return DEFAULT_PAYMENT_METHODS.copy()
    return SUPPORTED_PAYMENT_METHODS_BY_COUNTRY.get(country, DEFAULT_PAYMENT_METHODS.copy())


def get_plan_price(country_code: Any, plan_code: Any, billing_cycle: Any) -> dict[str, Any]:
    plan = normalize_plan_code(plan_code)
    billing = normalize_billing_cycle(billing_cycle)
    country = _normalize_text(country_code).upper() or DEFAULT_COUNTRY

    if plan == PLAN_TRIAL:
        return {"price": Decimal("0"), "currency": COUNTRY_CURRENCY.get(country, DEFAULT_CURRENCY)}

    country_prices = PRICE_MATRIX.get(country)
    if country_prices and plan in country_prices and billing in country_prices[plan]:
        return {"price": country_prices[plan][billing], "currency": COUNTRY_CURRENCY.get(country, DEFAULT_CURRENCY)}

    fallback_prices = PRICE_MATRIX.get(DEFAULT_COUNTRY, {})
    if plan in fallback_prices and billing in fallback_prices[plan]:
        return {"price": fallback_prices[plan][billing], "currency": COUNTRY_CURRENCY.get(DEFAULT_COUNTRY, DEFAULT_CURRENCY)}

    return {"price": Decimal("0"), "currency": COUNTRY_CURRENCY.get(country, DEFAULT_CURRENCY)}


def get_months_paid(billing_cycle: Any) -> int:
    return MONTHS_BY_BILLING_CYCLE.get(normalize_billing_cycle(billing_cycle), 1)


def get_plan_billing_periods(plan_code: Any) -> list[str]:
    plan = normalize_plan_code(plan_code)
    if plan == PLAN_TRIAL:
        return [BILLING_MONTHLY]
    return [BILLING_MONTHLY, BILLING_ANNUAL]
