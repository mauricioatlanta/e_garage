import json
import logging
from json import JSONDecodeError

from django.conf import settings
from django.db import IntegrityError, connection
from django.db import transaction
from django.utils import timezone

from taller.country.engine import URL_SLUG_TO_VERTICAL
from taller.middleware.rate_limiting import rate_limiter
from taller.models.public_analytics_event import PublicAnalyticsEvent
from taller.models.public_analytics_session import PublicAnalyticsSession
from taller.services.public_attribution import (
    SESSION_COOKIE,
    find_first_touch_session_for_request,
    hash_public_analytics_value,
    metadata_size,
)
from taller.utils.smart_logging import get_client_ip


DESARMADURIA_PATH = "/cl/desarmadurias/"
DESARMADURIA_VERTICAL = "salvage"
DESARMADURIA_COUNTRY = "cl"

logger = logging.getLogger(__name__)

PUBLIC_ENDPOINT_EVENT_TYPES = {
    PublicAnalyticsEvent.EVENT_SCROLL_50,
    PublicAnalyticsEvent.EVENT_SCROLL_90,
    PublicAnalyticsEvent.EVENT_CTA_CLICK,
    PublicAnalyticsEvent.EVENT_CTA_WHATSAPP_CLICK,
    PublicAnalyticsEvent.EVENT_CTA_TRIAL_30_CLICK,
}

BACKEND_EVENT_TYPES = {
    PublicAnalyticsEvent.EVENT_HUMAN_VISIT,
    PublicAnalyticsEvent.EVENT_SIGNUP_STARTED,
    PublicAnalyticsEvent.EVENT_SIGNUP_COMPLETED,
    PublicAnalyticsEvent.EVENT_COMPANY_CREATED,
    PublicAnalyticsEvent.EVENT_FIRST_LOGIN,
}

ALLOWED_METADATA_KEYS = {
    PublicAnalyticsEvent.EVENT_SCROLL_50: {"scroll_percent", "viewport_height", "document_height"},
    PublicAnalyticsEvent.EVENT_SCROLL_90: {"scroll_percent", "viewport_height", "document_height"},
    PublicAnalyticsEvent.EVENT_CTA_CLICK: {"cta_id", "cta_label", "href"},
    PublicAnalyticsEvent.EVENT_CTA_WHATSAPP_CLICK: {"cta_id", "cta_label", "href"},
    PublicAnalyticsEvent.EVENT_CTA_TRIAL_30_CLICK: {"cta_id", "cta_label", "href"},
}

BACKEND_ALLOWED_METADATA_KEYS = {
    PublicAnalyticsEvent.EVENT_SIGNUP_STARTED: {"source", "source_path"},
}

SENSITIVE_CLIENT_KEYS = {
    "is_bot",
    "is_internal",
    "country",
    "vertical",
    "vertical_key",
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
    "msclkid",
}


class PublicEventValidationError(ValueError):
    def __init__(self, code: str, status: int = 400):
        self.code = code
        self.status = status
        super().__init__(code)


def _payload_limit() -> int:
    return int(getattr(settings, "PUBLIC_ANALYTICS_PAYLOAD_MAX_BYTES", 4096))


def _metadata_limit() -> int:
    return int(getattr(settings, "PUBLIC_ANALYTICS_METADATA_MAX_BYTES", 1024))


def _vertical_from_path(path: str) -> str:
    parts = [part for part in (path or "").split("/") if part]
    for part in reversed(parts):
        vertical = URL_SLUG_TO_VERTICAL.get(part)
        if vertical:
            return vertical
    return ""


def _configure_public_rate_limit():
    rate_limiter.limits["public_analytics_event"] = {
        "attempts": int(getattr(settings, "PUBLIC_ANALYTICS_RATE_LIMIT_ATTEMPTS", 60)),
        "window": int(getattr(settings, "PUBLIC_ANALYTICS_RATE_LIMIT_WINDOW", 60)),
        "block_time": int(getattr(settings, "PUBLIC_ANALYTICS_RATE_LIMIT_WINDOW", 60)),
    }


def check_public_event_rate_limit(request, session_hash: str) -> tuple[bool, int]:
    _configure_public_rate_limit()

    identifiers = []
    ip = get_client_ip(request) or ""
    if ip:
        try:
            identifiers.append(f"ip:{hash_public_analytics_value(ip)}")
        except RuntimeError:
            pass
    if session_hash:
        identifiers.append(f"session:{session_hash}")

    for identifier in identifiers:
        allowed, _attempts_left, reset_time = rate_limiter.check_rate_limit(
            "public_analytics_event",
            identifier,
        )
        if not allowed:
            return False, max(1, int(reset_time - timezone.now().timestamp()))

    return True, 0


def parse_public_event_payload(request) -> dict:
    if request.content_type != "application/json":
        raise PublicEventValidationError("unsupported_media_type", status=415)

    body = request.body or b""
    if len(body) > _payload_limit():
        raise PublicEventValidationError("payload_too_large", status=413)

    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, JSONDecodeError):
        raise PublicEventValidationError("invalid_json")

    if not isinstance(payload, dict):
        raise PublicEventValidationError("invalid_payload")

    if set(payload) & SENSITIVE_CLIENT_KEYS:
        raise PublicEventValidationError("sensitive_client_fields_rejected")

    return payload


def validate_public_event_payload(payload: dict) -> tuple[str, str, str, dict]:
    event_type = (payload.get("event_type") or "").strip()
    if event_type not in PUBLIC_ENDPOINT_EVENT_TYPES:
        raise PublicEventValidationError("event_type_not_allowed")

    path = (payload.get("path") or "").strip()
    if event_type == PublicAnalyticsEvent.EVENT_CTA_CLICK:
        if path != "/":
            raise PublicEventValidationError("path_not_allowed")
    elif path != DESARMADURIA_PATH:
        raise PublicEventValidationError("path_not_allowed")

    vertical = _vertical_from_path(path)
    if event_type != PublicAnalyticsEvent.EVENT_CTA_CLICK and vertical != DESARMADURIA_VERTICAL:
        raise PublicEventValidationError("vertical_not_allowed")

    metadata = payload.get("metadata") or {}
    if not isinstance(metadata, dict):
        raise PublicEventValidationError("invalid_metadata")
    if metadata_size(metadata) > _metadata_limit():
        raise PublicEventValidationError("metadata_too_large", status=413)
    if len(metadata) > 10:
        raise PublicEventValidationError("metadata_too_many_keys")
    if set(metadata) - ALLOWED_METADATA_KEYS[event_type]:
        raise PublicEventValidationError("metadata_keys_not_allowed")

    clean_metadata = {}
    for key, value in metadata.items():
        if isinstance(value, (int, float, bool)):
            clean_metadata[key] = value
        elif isinstance(value, str):
            clean_metadata[key] = value[:200]
        else:
            raise PublicEventValidationError("metadata_value_not_allowed")

    if metadata_size(clean_metadata) > _metadata_limit():
        raise PublicEventValidationError("metadata_too_large", status=413)

    dedupe_key = (payload.get("dedupe_key") or path).strip()[:120]
    if not dedupe_key:
        dedupe_key = path

    return event_type, path, dedupe_key, clean_metadata


def get_session_from_request_cookie(request):
    raw_session_id = request.COOKIES.get(SESSION_COOKIE)
    if not raw_session_id:
        return None

    try:
        session_hash = hash_public_analytics_value(raw_session_id)
    except RuntimeError:
        return None

    return PublicAnalyticsSession.objects.filter(
        anonymous_session_hash=session_hash,
        expires_at__gt=timezone.now(),
    ).first()


def record_public_event(
    *,
    session: PublicAnalyticsSession,
    event_type: str,
    path: str,
    dedupe_key: str,
    metadata: dict | None = None,
    page_view=None,
):
    try:
        event, created = PublicAnalyticsEvent.objects.get_or_create(
            session=session,
            event_type=event_type,
            dedupe_key=dedupe_key[:120],
            defaults={
                "page_view": page_view,
                "path": path[:255],
                "metadata": metadata or {},
                "occurred_at": timezone.now(),
            },
        )
        return event, created
    except IntegrityError:
        return (
            PublicAnalyticsEvent.objects.get(
                session=session,
                event_type=event_type,
                dedupe_key=dedupe_key[:120],
            ),
            False,
        )


def _is_valid_desarmaduria_attribution(session: PublicAnalyticsSession) -> bool:
    if session is None:
        return False
    if session.is_bot or session.is_internal:
        return False
    if session.vertical_key != DESARMADURIA_VERTICAL:
        return False
    if session.country != DESARMADURIA_COUNTRY:
        return False
    if DESARMADURIA_PATH not in {session.landing_path, session.first_path}:
        return False

    cutoff = timezone.now() - timezone.timedelta(
        days=int(getattr(settings, "PUBLIC_ANALYTICS_ATTRIBUTION_DAYS", 30))
    )
    return session.first_seen_at >= cutoff and session.expires_at > timezone.now()


def record_signup_started_from_request(request):
    """
    Registra signup_started desde backend, sin interrumpir el render de signup.
    """
    try:
        session = find_first_touch_session_for_request(
            request,
            country=DESARMADURIA_COUNTRY,
            vertical_key=DESARMADURIA_VERTICAL,
            path=DESARMADURIA_PATH,
            active_only=True,
        )
        if not _is_valid_desarmaduria_attribution(session):
            return None, False

        metadata = {"source": "backend", "source_path": DESARMADURIA_PATH}
        if set(metadata) - BACKEND_ALLOWED_METADATA_KEYS[PublicAnalyticsEvent.EVENT_SIGNUP_STARTED]:
            return None, False

        return record_public_event(
            session=session,
            event_type=PublicAnalyticsEvent.EVENT_SIGNUP_STARTED,
            path=(request.path or "")[:255],
            dedupe_key=PublicAnalyticsEvent.EVENT_SIGNUP_STARTED,
            metadata=metadata,
        )
    except Exception:
        logger.exception(
            "public_analytics: error tracking signup_started path=%s",
            getattr(request, "path", ""),
        )
        return None, False


def record_signup_completed_from_request(request, user, country):
    """
    Atribuye un signup ya persistido y registra signup_completed.

    Si la llamada ocurre dentro de una transacción, el callback espera al commit
    para no registrar una conversión que luego sea revertida.
    """
    def _record():
        try:
            session = find_first_touch_session_for_request(
                request,
                country=DESARMADURIA_COUNTRY,
                vertical_key=DESARMADURIA_VERTICAL,
                path=DESARMADURIA_PATH,
                active_only=True,
            )
            if not _is_valid_desarmaduria_attribution(session):
                return None, False

            from taller.services.registro_embudo_service import registrar_signup

            embudo = registrar_signup(
                user=user,
                pais=country,
                public_session=session,
            )
            if embudo is None:
                return None, False

            event_session = embudo.public_session or session
            return record_public_event(
                session=event_session,
                event_type=PublicAnalyticsEvent.EVENT_SIGNUP_COMPLETED,
                path=(request.path or "")[:255],
                dedupe_key=PublicAnalyticsEvent.EVENT_SIGNUP_COMPLETED,
                metadata={"source": "backend"},
            )
        except Exception:
            logger.exception(
                "public_analytics: error tracking signup_completed user_id=%s path=%s",
                getattr(user, "pk", None),
                getattr(request, "path", ""),
            )
            return None, False

    try:
        if transaction.get_autocommit() or not connection.in_atomic_block:
            return _record()
        transaction.on_commit(_record)
    except Exception:
        logger.exception(
            "public_analytics: unable to schedule signup_completed user_id=%s",
            getattr(user, "pk", None),
        )
    return None, False


def record_company_created_for_user(user):
    """
    Registra company_created usando exclusivamente la sesión ya vinculada al embudo.
    """
    def _record():
        try:
            from taller.models.registro_embudo import RegistroEmbudoSuscriptor

            embudo = (
                RegistroEmbudoSuscriptor.objects.select_related("public_session")
                .filter(user=user)
                .first()
            )
            if not embudo or not embudo.empresa_creada_at or not embudo.public_session_id:
                return None, False
            if not _is_valid_desarmaduria_attribution(embudo.public_session):
                return None, False

            return record_public_event(
                session=embudo.public_session,
                event_type=PublicAnalyticsEvent.EVENT_COMPANY_CREATED,
                path="/backend/empresa/",
                dedupe_key=PublicAnalyticsEvent.EVENT_COMPANY_CREATED,
                metadata={"source": "backend"},
            )
        except Exception:
            logger.exception(
                "public_analytics: error tracking company_created user_id=%s",
                getattr(user, "pk", None),
            )
            return None, False

    try:
        if transaction.get_autocommit() or not connection.in_atomic_block:
            return _record()
        transaction.on_commit(_record)
    except Exception:
        logger.exception(
            "public_analytics: unable to schedule company_created user_id=%s",
            getattr(user, "pk", None),
        )
    return None, False


def is_internal_first_login_request(user, request=None):
    """Return whether a successful login belongs to internal/QA traffic."""
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True

    email = (getattr(user, "email", "") or "").strip().lower()
    qa_domain = str(
        getattr(settings, "PUBLIC_ANALYTICS_QA_EMAIL_DOMAIN", "egarage.test")
    ).strip().lower().lstrip("@")
    if qa_domain and email.endswith(f"@{qa_domain}"):
        return True

    if request is None:
        return False

    if (getattr(request, "COOKIES", {}) or {}).get("eg_internal_traffic") == "1":
        return True
    if getattr(request, "qa_control_context", None):
        return True

    session = getattr(request, "session", None)
    if session is not None and session.get("qa_control"):
        return True

    # No impersonation flow is currently registered in eGarage. These markers
    # are preventive only for a future auth adapter; they are not production
    # impersonation state today.
    return any(
        bool(getattr(request, marker, False))
        for marker in ("is_impersonating", "impersonating", "impersonator")
    )


def record_first_login_for_user(user):
    """
    Record first_login from the funnel's already persisted public_session.

    This function never recalculates attribution from cookies or request data.
    """
    def _record():
        try:
            from taller.models.registro_embudo import RegistroEmbudoSuscriptor

            embudo = (
                RegistroEmbudoSuscriptor.objects.select_related("public_session")
                .filter(user=user)
                .first()
            )
            if not embudo or not embudo.public_session_id:
                return None, False
            if not _is_valid_desarmaduria_attribution(embudo.public_session):
                return None, False

            return record_public_event(
                session=embudo.public_session,
                event_type=PublicAnalyticsEvent.EVENT_FIRST_LOGIN,
                path="/backend/login/",
                dedupe_key=PublicAnalyticsEvent.EVENT_FIRST_LOGIN,
                metadata={"source": "backend"},
            )
        except Exception:
            logger.exception(
                "public_analytics: error tracking first_login user_id=%s",
                getattr(user, "pk", None),
            )
            return None, False

    try:
        if transaction.get_autocommit() or not connection.in_atomic_block:
            return _record()
        transaction.on_commit(_record)
    except Exception:
        logger.exception(
            "public_analytics: unable to schedule first_login user_id=%s",
            getattr(user, "pk", None),
        )
    return None, False
