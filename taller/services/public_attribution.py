import hmac
import json
import uuid
from hashlib import sha256
from urllib.parse import urlparse

from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from taller.country.engine import URL_SLUG_TO_VERTICAL
from taller.models.public_analytics_session import PublicAnalyticsSession
from taller.models.public_page_view import is_probable_bot
from taller.services.public_analytics import _clean_referrer, _is_mobile
from taller.utils.smart_logging import get_client_ip


VISITOR_COOKIE = "eg_visitor_id"
SESSION_COOKIE = "eg_session_id"
ATTRIBUTION_DAYS = 30
SESSION_IDLE_MINUTES = 30

UTM_FIELDS = (
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "gclid",
    "fbclid",
    "msclkid",
)


def hash_public_analytics_value(raw_value: str) -> str:
    key = getattr(settings, "PUBLIC_ANALYTICS_HASH_KEY", "")
    if not key:
        raise RuntimeError("PUBLIC_ANALYTICS_HASH_KEY is required for public analytics hashing")

    return hmac.new(
        key.encode("utf-8"),
        (raw_value or "").encode("utf-8", errors="replace"),
        sha256,
    ).hexdigest()


def _new_cookie_value() -> str:
    return uuid.uuid4().hex


def _cookie_max_age() -> int:
    days = int(getattr(settings, "PUBLIC_ANALYTICS_ATTRIBUTION_DAYS", ATTRIBUTION_DAYS))
    return days * 24 * 60 * 60


def _session_idle_seconds() -> int:
    minutes = int(
        getattr(settings, "PUBLIC_ANALYTICS_SESSION_IDLE_MINUTES", SESSION_IDLE_MINUTES)
    )
    return minutes * 60


def _cookie_secure() -> bool:
    return bool(getattr(settings, "PUBLIC_ANALYTICS_COOKIE_SECURE", not settings.DEBUG))


def _set_cookie(response, name: str, value: str, max_age: int):
    response.set_cookie(
        name,
        value,
        max_age=max_age,
        httponly=True,
        secure=_cookie_secure(),
        samesite="Lax",
    )


def attach_public_analytics_cookies(request, response):
    pending = getattr(request, "_public_analytics_pending_cookies", {})
    for name, value in pending.items():
        max_age = _session_idle_seconds() if name == SESSION_COOKIE else _cookie_max_age()
        _set_cookie(response, name, value, max_age)
    return response


def _extract_utm(request) -> dict:
    result = {}
    for field in UTM_FIELDS:
        value = (request.GET.get(field) or "").strip()
        if value:
            max_length = PublicAnalyticsSession._meta.get_field(field).max_length
            result[field] = value[:max_length]
    return result


def _attribution_type(utm: dict, referrer: str) -> str:
    if any(utm.get(field) for field in ("gclid", "fbclid", "msclkid")):
        return PublicAnalyticsSession.ATTRIBUTION_PAID_CLICK_ID
    if any(utm.get(field) for field in ("utm_source", "utm_medium", "utm_campaign")):
        return PublicAnalyticsSession.ATTRIBUTION_UTM
    if referrer:
        return PublicAnalyticsSession.ATTRIBUTION_REFERRER
    return PublicAnalyticsSession.ATTRIBUTION_DIRECT


def _vertical_from_path(path: str) -> str:
    parts = [part for part in (path or "").split("/") if part]
    for part in reversed(parts):
        vertical = URL_SLUG_TO_VERTICAL.get(part)
        if vertical:
            return vertical
    return ""


def _is_internal_request(request, ip_hash: str) -> bool:
    if request.COOKIES.get("eg_internal_traffic") == "1":
        return True

    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        email = (getattr(user, "email", "") or "").lower()
        if getattr(user, "is_superuser", False):
            return True
        if getattr(user, "is_staff", False):
            return True
        if email.endswith("@egarage.test"):
            return True

    ip = get_client_ip(request) or ""
    excluded_ips = set(getattr(settings, "PUBLIC_ANALYTICS_EXCLUDED_IPS", []) or [])
    if ip and ip in excluded_ips:
        return True

    excluded_hashes = set(getattr(settings, "PUBLIC_ANALYTICS_EXCLUDED_IP_HASHES", []) or [])
    return bool(ip_hash and ip_hash in excluded_hashes)


def _current_cookie_hashes(request) -> tuple[str, str, str, str]:
    visitor_cookie = request.COOKIES.get(VISITOR_COOKIE) or _new_cookie_value()
    session_cookie = request.COOKIES.get(SESSION_COOKIE) or _new_cookie_value()

    request._public_analytics_pending_cookies = {
        VISITOR_COOKIE: visitor_cookie,
        SESSION_COOKIE: session_cookie,
    }

    return (
        visitor_cookie,
        session_cookie,
        hash_public_analytics_value(visitor_cookie),
        hash_public_analytics_value(session_cookie),
    )


def get_or_create_public_session(
    request,
    *,
    page_type: str = "",
    country: str = "",
    language: str = "",
    vertical_key: str = "",
):
    try:
        visitor_cookie, session_cookie, visitor_hash, session_hash = _current_cookie_hashes(request)
        now = timezone.now()
        user_agent = (request.META.get("HTTP_USER_AGENT") or "")[:500]
        referrer = _clean_referrer(request)
        ip = get_client_ip(request) or ""
        ip_hash = hash_public_analytics_value(ip) if ip else ""
        path = request.path[:255]
        utm = _extract_utm(request)
        vertical = (vertical_key or _vertical_from_path(path) or "")[:40]

        session = PublicAnalyticsSession.objects.filter(
            anonymous_session_hash=session_hash,
            expires_at__gt=now,
        ).first()

        idle_cutoff = now - timezone.timedelta(seconds=_session_idle_seconds())
        if session and session.last_seen_at < idle_cutoff:
            session_cookie = _new_cookie_value()
            session_hash = hash_public_analytics_value(session_cookie)
            request._public_analytics_pending_cookies = {
                **getattr(request, "_public_analytics_pending_cookies", {}),
                SESSION_COOKIE: session_cookie,
            }
            session = None

        is_bot = is_probable_bot(user_agent)
        is_internal = _is_internal_request(request, ip_hash)
        expires_at = now + timezone.timedelta(seconds=_cookie_max_age())

        if session is None:
            session = PublicAnalyticsSession.objects.create(
                anonymous_visitor_hash=visitor_hash,
                anonymous_session_hash=session_hash,
                first_path=path,
                last_path=path,
                landing_path=path if page_type else "",
                country=(country or "").lower()[:8],
                language=(language or "").lower()[:8],
                vertical_key=vertical,
                page_type=(page_type or "")[:20],
                initial_referrer=referrer,
                last_referrer=referrer,
                attribution_type=_attribution_type(utm, referrer),
                user_agent=user_agent,
                is_mobile=_is_mobile(user_agent),
                is_bot=is_bot,
                is_internal=is_internal,
                ip_hash=ip_hash,
                first_seen_at=now,
                last_seen_at=now,
                expires_at=expires_at,
                **utm,
            )
        else:
            update_fields = ["last_path", "last_referrer", "last_seen_at", "expires_at", "updated_at"]
            session.last_path = path
            session.last_referrer = referrer
            session.last_seen_at = now
            session.expires_at = expires_at
            if not session.is_bot and is_bot:
                session.is_bot = True
                update_fields.append("is_bot")
            if not session.is_internal and is_internal:
                session.is_internal = True
                update_fields.append("is_internal")
            session.save(update_fields=update_fields)

        return session
    except RuntimeError:
        request._public_analytics_pending_cookies = {}
        return None


def find_first_touch_session_for_request(
    request,
    *,
    country: str = "",
    vertical_key: str = "",
    path: str = "",
    active_only: bool = False,
):
    try:
        visitor_cookie = request.COOKIES.get(VISITOR_COOKIE)
        if not visitor_cookie:
            return None

        visitor_hash = hash_public_analytics_value(visitor_cookie)
        now = timezone.now()
        cutoff = timezone.now() - timezone.timedelta(
            days=int(getattr(settings, "PUBLIC_ANALYTICS_ATTRIBUTION_DAYS", ATTRIBUTION_DAYS))
        )
        filters = {
            "anonymous_visitor_hash": visitor_hash,
            "first_seen_at__gte": cutoff,
            "is_bot": False,
            "is_internal": False,
        }
        if active_only:
            filters["expires_at__gt"] = now
        if country:
            filters["country"] = country.lower()
        if vertical_key:
            filters["vertical_key"] = vertical_key

        attributed = PublicAnalyticsSession.objects.filter(**filters).exclude(
            attribution_type=PublicAnalyticsSession.ATTRIBUTION_UNKNOWN
        )
        if path:
            attributed = attributed.filter(Q(landing_path=path) | Q(first_path=path))

        attributed = attributed.order_by("first_seen_at")
        return attributed.first()
    except RuntimeError:
        return None


def metadata_size(metadata: dict) -> int:
    return len(json.dumps(metadata, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))
