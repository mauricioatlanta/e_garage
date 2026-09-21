import logging
import hashlib
import uuid
from datetime import timedelta
from urllib.parse import urlparse

from django.conf import settings
from django.utils import timezone

from taller.country.engine import URL_SLUG_TO_VERTICAL
from taller.models.public_page_view import PublicAnalyticsEvent, PublicPageView, is_probable_bot
from taller.models.public_analytics_session import PublicAnalyticsSession
from taller.utils.smart_logging import get_client_ip


logger = logging.getLogger(__name__)

ANALYTICS_SESSION_KEY = "eg_analytics_session_id"
ANALYTICS_ATTRIBUTION_KEY = "eg_analytics_attribution"

UTM_KEYS = ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term")
KNOWN_COUNTRY_SLUGS = {"cl", "us", "mx", "pe", "ar", "br", "co", "uy", "ve", "ec"}
KNOWN_LANGUAGE_SLUGS = {"es", "en", "pt"}
IGNORED_PATH_PREFIXES = (
    "/health",
    "/health-simple",
    "/healthz",
    "/static/",
    "/media/",
    "/favicon",
    "/robots.txt",
    "/sitemap.xml",
    "/admin/jsi18n/",
)


def _is_mobile(user_agent: str) -> bool:
    ua = (user_agent or "").lower()
    return any(
        token in ua
        for token in (
            "mobile",
            "android",
            "iphone",
            "ipad",
            "ipod",
        )
    )


def _primary_browser_language(request) -> str:
    accept_language = (request.META.get("HTTP_ACCEPT_LANGUAGE") or "").strip()
    for raw_part in accept_language.split(","):
        token = raw_part.split(";", 1)[0].strip().lower()
        if not token:
            continue
        return token.split("-", 1)[0][:8]
    return ""


def _country_from_path(path: str) -> str:
    parts = [part.lower() for part in (path or "").split("/") if part]
    if parts and parts[0] in KNOWN_COUNTRY_SLUGS:
        return parts[0]
    return ""


def _language_from_path(path: str) -> str:
    parts = [part.lower() for part in (path or "").split("/") if part]
    if len(parts) >= 2 and parts[1] in KNOWN_LANGUAGE_SLUGS:
        return parts[1]
    return ""


def _inferred_country(request, explicit_country: str = "", empresa=None) -> str:
    candidates = (
        explicit_country,
        getattr(request, "country", ""),
        getattr(request, "country_code", ""),
        request.META.get("HTTP_CF_IPCOUNTRY", ""),
        request.META.get("HTTP_X_VERCEL_IP_COUNTRY", ""),
        _country_from_path(getattr(request, "path", "")),
        getattr(empresa, "pais", ""),
    )
    for value in candidates:
        value = (value or "").strip().lower()
        if value and value != "xx":
            return value[:8]
    return ""


def _inferred_language(request, explicit_language: str = "") -> str:
    candidates = (
        explicit_language,
        _language_from_path(getattr(request, "path", "")),
        getattr(request, "LANGUAGE_CODE", ""),
        request.GET.get("lang", ""),
        _primary_browser_language(request),
    )
    for value in candidates:
        value = (value or "").strip().lower()
        if value:
            return value.split("-", 1)[0][:8]
    return ""


def _session_id(request) -> str:
    session_id = request.session.get(ANALYTICS_SESSION_KEY)
    if not session_id:
        session_id = uuid.uuid4().hex
        request.session[ANALYTICS_SESSION_KEY] = session_id
        request.session.modified = True
        if hasattr(request.session, "set_expiry"):
            request.session.set_expiry(30 * 24 * 60 * 60)
    return session_id


def _runtime_session_hash(session_key: str) -> str:
    namespace = "runtime-public-analytics-session:v1:"
    secret = getattr(settings, "PUBLIC_ANALYTICS_HASH_KEY", "") or ""
    return hashlib.sha256(f"{namespace}{secret}:{session_key}".encode("utf-8")).hexdigest()


def get_or_create_public_session(request, *, page_type="", country="", language="", now=None):
    """Resolve the durable first-party session while retaining legacy fields."""
    now = now or timezone.now()
    session_key = _session_id(request)
    attribution = _current_attribution(request, referrer=_clean_referrer(request))
    user_agent = (request.META.get("HTTP_USER_AGENT") or "")[:500]
    ip = get_client_ip(request) or ""
    quality = _quality_flags(request, ip=ip, user_agent=user_agent)
    country = _inferred_country(request, country)
    language = _inferred_language(request, language)
    visitor_hash = PublicPageView.build_visitor_hash(ip, user_agent, now.date().isoformat())
    defaults = {
        "anonymous_visitor_hash": visitor_hash,
        "first_path": request.path[:255],
        "last_path": request.path[:255],
        "landing_path": attribution["landing_initial"][:255],
        "country": country,
        "language": language,
        "vertical_key": _rubro_from_path(request.path)[:40],
        "page_type": page_type,
        "initial_referrer": attribution["referrer"],
        "last_referrer": attribution["referrer"],
        "utm_source": attribution["utm_source"][:100],
        "utm_medium": attribution["utm_medium"][:100],
        "utm_campaign": attribution["utm_campaign"][:150],
        "utm_term": attribution["utm_term"][:150],
        "utm_content": attribution["utm_content"][:150],
        "attribution_type": "utm" if attribution["utm_source"] else ("referrer" if attribution["referrer"] else "direct"),
        "user_agent": user_agent,
        "is_mobile": _is_mobile(user_agent),
        "is_bot": quality["is_bot"],
        "is_internal": quality["is_internal"],
        "ip_hash": "",
        "first_seen_at": now,
        "last_seen_at": now,
        "expires_at": now + timedelta(days=30),
    }
    session, created = PublicAnalyticsSession.objects.get_or_create(
        anonymous_session_hash=_runtime_session_hash(session_key),
        defaults=defaults,
    )
    if not created:
        PublicAnalyticsSession.objects.filter(pk=session.pk).update(
            last_path=request.path[:255],
            last_referrer=attribution["referrer"],
            last_seen_at=now,
        )
        session.last_path = request.path[:255]
        session.last_referrer = attribution["referrer"]
        session.last_seen_at = now
    return session


def _path_should_be_ignored(path: str) -> bool:
    path = path or ""
    return any(path.startswith(prefix) for prefix in IGNORED_PATH_PREFIXES)


def _is_staff_request(request) -> bool:
    user = getattr(request, "user", None)
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))
    )


def _is_server_ip(ip: str) -> bool:
    ip = (ip or "").strip()
    if not ip:
        return False

    server_ips = {
        "127.0.0.1",
        "::1",
        "localhost",
        getattr(settings, "CUSTOM_DOMAIN_VPS_IP", ""),
        getattr(settings, "EGARAGE_CUSTOM_DOMAIN_VPS_IP", ""),
    }
    return ip in {value for value in server_ips if value}


def _source_from_referrer(referrer: str) -> str:
    if not referrer:
        return "Directo / sin referrer"

    netloc = urlparse(referrer).netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]

    if not netloc:
        return "Directo / sin referrer"
    if "google." in netloc:
        return "Google"
    if "bing." in netloc:
        return "Bing"
    if "facebook." in netloc or "instagram." in netloc:
        return "Meta"
    if "tiktok." in netloc:
        return "TikTok"
    if "linkedin." in netloc:
        return "LinkedIn"
    if "egarage.cl" in netloc:
        return "eGarage interno"
    return netloc


def _normalized_utm_source(source: str) -> str:
    source = (source or "").strip().lower()
    if source in {"fb", "facebook", "meta", "ig", "instagram"}:
        return "facebook" if source in {"fb", "facebook"} else source
    if source in {"tiktok", "tt"}:
        return "tiktok"
    if source in {"google", "google_ads", "adwords"}:
        return "google"
    if source in {"whatsapp", "wa"}:
        return "whatsapp"
    return source


def _source_label(request, referrer: str) -> str:
    source = _normalized_utm_source(request.GET.get("utm_source"))
    medium = (request.GET.get("utm_medium") or "").strip().lower()
    if source and medium:
        return f"{source} / {medium}"[:120]
    if source:
        return source[:120]
    return _source_from_referrer(referrer)[:120]


def _rubro_from_path(path: str) -> str:
    parts = [part for part in (path or "").split("/") if part]
    for part in reversed(parts):
        vertical = URL_SLUG_TO_VERTICAL.get(part)
        if vertical:
            return vertical
    return ""


def _current_attribution(request, *, referrer: str = "") -> dict:
    stored = dict(request.session.get(ANALYTICS_ATTRIBUTION_KEY) or {})
    path = (request.path or "")[:255]

    captured = {
        key: (request.GET.get(key) or "").strip()[:160]
        for key in UTM_KEYS
    }
    has_utm = any(captured.values())

    if has_utm or not stored:
        stored.update(captured)
        stored["landing_initial"] = stored.get("landing_initial") or path
        stored["referrer"] = (referrer or stored.get("referrer") or "")[:500]
        stored["source_label"] = _source_label(request, referrer)
        request.session[ANALYTICS_ATTRIBUTION_KEY] = stored
        request.session.modified = True

    return {
        "utm_source": stored.get("utm_source", "")[:120],
        "utm_medium": stored.get("utm_medium", "")[:120],
        "utm_campaign": stored.get("utm_campaign", "")[:160],
        "utm_content": stored.get("utm_content", "")[:160],
        "utm_term": stored.get("utm_term", "")[:160],
        "landing_initial": stored.get("landing_initial", path)[:255],
        "referrer": (referrer or stored.get("referrer", ""))[:500],
        "source_label": (stored.get("source_label") or _source_label(request, referrer))[:120],
    }


def _clean_referrer(request) -> str:
    raw = (request.META.get("HTTP_REFERER") or "").strip()[:1000]
    if not raw:
        return ""

    try:
        parsed = urlparse(raw)
        if not parsed.netloc:
            return raw[:500]
        value = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return value[:500]
    except Exception:
        return raw[:500]


def _quality_flags(request, *, ip: str, user_agent: str) -> dict:
    is_staff = _is_staff_request(request)
    is_server = _is_server_ip(ip)
    is_bot = is_probable_bot(user_agent)
    return {
        "is_bot": is_bot,
        "is_staff": is_staff,
        "is_server": is_server,
        "is_internal": bool(is_staff or is_server),
    }


def track_public_page(
    request,
    *,
    page_type: str,
    country: str = "",
    language: str = "",
):
    """
    Registra una visualización pública.

    Fallar analytics nunca debe interrumpir una landing pública.
    """
    try:
        if request.method != "GET":
            return None
        if _path_should_be_ignored(getattr(request, "path", "")):
            return None

        user_agent = (request.META.get("HTTP_USER_AGENT") or "")[:500]
        ip = get_client_ip(request) or ""
        referrer = _clean_referrer(request)
        attribution = _current_attribution(request, referrer=referrer)
        quality = _quality_flags(request, ip=ip, user_agent=user_agent)
        session_id = _session_id(request)
        inferred_country = _inferred_country(request, country)
        inferred_language = _inferred_language(request, language)
        now = timezone.now()
        public_session = get_or_create_public_session(
            request,
            page_type=page_type,
            country=inferred_country,
            language=inferred_language,
            now=now,
        )

        visitor_hash = PublicPageView.build_visitor_hash(
            ip=ip,
            user_agent=user_agent,
            date_key=now.date().isoformat(),
        )

        page_view = PublicPageView.objects.create(
            path=request.path[:255],
            page_type=page_type,
            country=inferred_country,
            language=inferred_language,
            visitor_hash=visitor_hash,
            session_key=session_id,
            public_session=public_session,
            referrer=referrer,
            user_agent=user_agent,
            is_mobile=_is_mobile(user_agent),
            is_bot=quality["is_bot"],
            is_staff=quality["is_staff"],
            is_server=quality["is_server"],
            is_internal=quality["is_internal"],
            utm_source=attribution["utm_source"],
            utm_medium=attribution["utm_medium"],
            utm_campaign=attribution["utm_campaign"],
            utm_content=attribution["utm_content"],
            utm_term=attribution["utm_term"],
            landing_initial=attribution["landing_initial"],
            source_label=attribution["source_label"],
            created_at=now,
        )
        if page_type == PublicPageView.PAGE_LANDING:
            create_public_event(
                request,
                PublicAnalyticsEvent.EVENT_LANDING_VIEW,
                page_view=page_view,
                country=inferred_country,
                language=inferred_language,
                rubro=_rubro_from_path(request.path),
            )
        return page_view
    except Exception:
        logger.exception(
            "public_analytics: error tracking path=%s",
            getattr(request, "path", ""),
        )
        return None


def create_public_event(
    request,
    event_type: str,
    *,
    page_view=None,
    empresa=None,
    country: str = "",
    language: str = "",
    rubro: str = "",
    metadata=None,
    value=None,
    currency: str = "",
):
    try:
        if _path_should_be_ignored(getattr(request, "path", "")):
            return None

        user_agent = (request.META.get("HTTP_USER_AGENT") or "")[:500]
        ip = get_client_ip(request) or ""
        referrer = _clean_referrer(request)
        attribution = _current_attribution(request, referrer=referrer)
        quality = _quality_flags(request, ip=ip, user_agent=user_agent)
        session_id = _session_id(request)
        now = timezone.now()
        public_session = getattr(page_view, "public_session", None) or get_or_create_public_session(
            request,
            country=country,
            language=language,
            now=now,
        )
        visitor_hash = PublicPageView.build_visitor_hash(
            ip=ip,
            user_agent=user_agent,
            date_key=now.date().isoformat(),
        )

        inferred_country = _inferred_country(request, country, empresa=empresa)
        inferred_language = _inferred_language(request, language)
        return PublicAnalyticsEvent.objects.create(
            event_type=event_type,
            page_view=page_view,
            session=public_session,
            empresa=empresa,
            path=(getattr(request, "path", "") or "")[:255],
            session_key=session_id,
            visitor_hash=visitor_hash,
            country=inferred_country,
            language=inferred_language,
            rubro=(rubro or _rubro_from_path(getattr(request, "path", "")))[:40],
            utm_source=attribution["utm_source"],
            utm_medium=attribution["utm_medium"],
            utm_campaign=attribution["utm_campaign"],
            utm_content=attribution["utm_content"],
            utm_term=attribution["utm_term"],
            landing_initial=attribution["landing_initial"],
            referrer=referrer,
            source_label=attribution["source_label"],
            is_mobile=_is_mobile(user_agent),
            is_bot=quality["is_bot"],
            is_staff=quality["is_staff"],
            is_server=quality["is_server"],
            is_internal=quality["is_internal"],
            value=value,
            currency=(currency or "")[:3],
            metadata=metadata or {},
            created_at=now,
            occurred_at=now,
        )
    except Exception:
        logger.exception(
            "public_analytics: error tracking event=%s path=%s",
            event_type,
            getattr(request, "path", ""),
        )
        return None


def track_model_event(
    *,
    event_type: str,
    empresa=None,
    path: str = "",
    source_label: str = "Sistema",
    metadata=None,
    value=None,
    currency: str = "",
):
    try:
        return PublicAnalyticsEvent.objects.create(
            event_type=event_type,
            empresa=empresa,
            path=(path or "")[:255],
            country=(getattr(empresa, "pais", "") or "").lower()[:8],
            source_label=source_label[:120],
            is_internal=False,
            is_staff=False,
            is_server=False,
            value=value,
            currency=(currency or "")[:3],
            metadata=metadata or {},
        )
    except Exception:
        logger.exception("public_analytics: error tracking model event=%s", event_type)
        return None
