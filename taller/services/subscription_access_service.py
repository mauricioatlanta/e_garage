from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from django.utils import timezone

from taller.utils.login_exempt import is_login_exempt_path

SubscriptionState = Literal["active", "grace", "restricted", "blocked"]


@dataclass(frozen=True)
class AccessDecision:
    state: SubscriptionState
    allow: bool
    warn: bool
    redirect_to: str | None = None
    reason: str | None = None


class SubscriptionAccessService:
    GRACE_DAYS = 5
    RESTRICTED_DAYS = 30

    COUNTRY_SEGMENTS = frozenset({"ar", "br", "cl", "co", "ec", "mx", "pe", "us", "uy", "ve"})
    LANGUAGE_SEGMENTS = frozenset({"en", "es", "pt"})

    SOFT_URLS = (
        "/documentos/",
        "/vehiculos/",
        "/clientes/",
        "/reportes/",
        "/servicios/",
    )

    HARD_URLS = (
        "/workspace/",
        "/dashboard/",
        "/centro-operaciones/",
        "/centro-operaciones-espacial/",
    )

    AUX_READONLY_URLS = (
        "/documentos/api/",
        "/ajax/",
    )

    EXEMPT_URLS = (
        "/accounts/",
        "/admin/",
        "/billing/",
        "/comprobante-pago/",
        "/contacto-ventas/",
        "/help/",
        "/legal/",
        "/media/",
        "/precios/",
        "/pricing/",
        "/soporte/",
        "/static/",
        "/subscription/",
        "/suscripcion/",
        "/support/",
        "/suspension/",
    )

    BILLING_URLS = {
        "CL": "/cl/es/suscripcion/pago/",
        "CO": "/co/es/suscripcion/pago/",
        "EC": "/ec/es/suscripcion/pago/",
        "MX": "/mx/es/suscripcion/pago/",
        "PE": "/pe/es/suscripcion/pago/",
        "US": "/us/en/subscription/payment/",
        "VE": "/ve/es/suscripcion/pago/",
    }

    @classmethod
    def get_subscription_state(cls, empresa) -> SubscriptionState:
        return cls.get_state(empresa)

    @classmethod
    def get_state(cls, empresa) -> SubscriptionState:
        if not empresa or not cls._is_enforcement_active(empresa):
            return "active"

        overdue_days = cls._get_overdue_days(empresa)
        if overdue_days is None:
            return "blocked"

        if overdue_days <= cls.GRACE_DAYS:
            return "grace"

        if overdue_days <= cls.RESTRICTED_DAYS:
            return "restricted"

        return "blocked"

    @classmethod
    def can_access_path(cls, empresa, path: str, method: str = "GET") -> bool:
        return cls.decide(empresa=empresa, path=path, method=method).allow

    @classmethod
    def get_billing_url(cls, empresa) -> str:
        country = (getattr(empresa, "pais", None) or "CL").upper()
        return cls.BILLING_URLS.get(country, cls.BILLING_URLS["CL"])

    @classmethod
    def decide(cls, empresa, path: str, method: str = "GET") -> AccessDecision:
        raw_path = cls._normalize_raw_path(path)
        base_path = cls.normalize_path(raw_path)
        method = (method or "GET").upper()
        state = cls.get_state(empresa)

        if cls.is_exempt_path(raw_path, base_path):
            return AccessDecision(
                state=state,
                allow=True,
                warn=state != "active",
                reason=None if state == "active" else f"{state}_exempt",
            )

        if state == "active":
            return AccessDecision(state=state, allow=True, warn=False)

        if state == "grace":
            return AccessDecision(state=state, allow=True, warn=True, reason="grace")

        billing_url = cls.get_billing_url(empresa)

        if state == "restricted":
            if method != "GET":
                return AccessDecision(
                    state=state,
                    allow=False,
                    warn=True,
                    redirect_to=billing_url,
                    reason="restricted_write_block",
                )

            if cls._matches_prefix(base_path, cls.SOFT_URLS):
                return AccessDecision(
                    state=state,
                    allow=True,
                    warn=True,
                    reason="restricted_soft",
                )

            if cls._matches_prefix(base_path, cls.AUX_READONLY_URLS):
                return AccessDecision(
                    state=state,
                    allow=True,
                    warn=True,
                    reason="restricted_aux_readonly",
                )

            if cls._matches_prefix(base_path, cls.HARD_URLS):
                return AccessDecision(
                    state=state,
                    allow=False,
                    warn=True,
                    redirect_to=billing_url,
                    reason="restricted_hard",
                )

            return AccessDecision(
                state=state,
                allow=False,
                warn=True,
                redirect_to=billing_url,
                reason="restricted_default",
            )

        reason = "blocked_default"
        if cls._matches_prefix(base_path, cls.SOFT_URLS):
            reason = "blocked_soft"
        elif cls._matches_prefix(base_path, cls.HARD_URLS):
            reason = "blocked_hard"

        return AccessDecision(
            state=state,
            allow=False,
            warn=True,
            redirect_to=billing_url,
            reason=reason,
        )

    @classmethod
    def is_exempt_path(cls, raw_path: str, base_path: str | None = None) -> bool:
        base_path = base_path or cls.normalize_path(raw_path)
        if raw_path == "/" or base_path == "/":
            return True
        if is_login_exempt_path(raw_path):
            return True
        return cls._matches_prefix(base_path, cls.EXEMPT_URLS)

    @classmethod
    def normalize_path(cls, path: str) -> str:
        raw_path = cls._normalize_raw_path(path)
        parts = [segment for segment in raw_path.split("/") if segment]

        if parts and parts[0].lower() in cls.COUNTRY_SEGMENTS:
            parts = parts[1:]

        if parts and parts[0].lower() in cls.LANGUAGE_SEGMENTS:
            parts = parts[1:]

        if not parts:
            return "/"

        normalized = "/" + "/".join(parts)
        if raw_path.endswith("/"):
            normalized += "/"
        return normalized

    @classmethod
    def _get_overdue_days(cls, empresa) -> int | None:
        expiration_date = cls._get_expiration_date(empresa)
        if expiration_date is None:
            return None
        now = timezone.now()
        today = timezone.localtime(now).date() if timezone.is_aware(now) else now.date()
        return max((today - expiration_date).days, 0)

    @staticmethod
    def _get_expiration_date(empresa) -> date | None:
        for attr_name in ("suscripcion_vence_el", "fecha_expiracion", "fecha_fin"):
            try:
                value = getattr(empresa, attr_name, None)
            except Exception:
                continue

            if value is None:
                continue

            if isinstance(value, datetime):
                if timezone.is_aware(value):
                    return timezone.localtime(value).date()
                return value.date()

            if isinstance(value, date):
                return value

        return None

    @staticmethod
    def _is_enforcement_active(empresa) -> bool:
        try:
            return bool(getattr(empresa, "debe_bloquear", False))
        except Exception:
            return False

    @staticmethod
    def _normalize_raw_path(path: str) -> str:
        path = (path or "/").strip()
        if not path:
            return "/"
        if not path.startswith("/"):
            path = f"/{path}"
        return path

    @classmethod
    def _matches_prefix(cls, path: str, prefixes: tuple[str, ...]) -> bool:
        normalized_path = cls._normalize_raw_path(path).rstrip("/") or "/"
        for prefix in prefixes:
            normalized_prefix = cls._normalize_raw_path(prefix).rstrip("/") or "/"
            if normalized_path == normalized_prefix:
                return True
            if normalized_path.startswith(f"{normalized_prefix}/"):
                return True
        return False


def get_subscription_state(empresa) -> SubscriptionState:
    return SubscriptionAccessService.get_subscription_state(empresa)


def can_access_path(empresa, path: str, method: str = "GET") -> bool:
    return SubscriptionAccessService.can_access_path(empresa, path, method)


def get_billing_url(empresa) -> str:
    return SubscriptionAccessService.get_billing_url(empresa)
