import logging
from urllib.parse import urlparse

from django.utils import timezone

from taller.models.public_page_view import PublicPageView, is_probable_bot
from taller.services.public_traffic_classifier import (
    is_canonical_public_host,
    is_probable_non_human_request,
    normalize_host,
)
from taller.utils.smart_logging import get_client_ip


logger = logging.getLogger(__name__)


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

        user_agent = (request.META.get("HTTP_USER_AGENT") or "")[:500]
        try:
            raw_host = request.get_host()
        except Exception:
            raw_host = request.META.get("HTTP_HOST", "")
        host = normalize_host(raw_host)
        ip = get_client_ip(request) or ""
        public_session = None
        try:
            from taller.services.public_attribution import get_or_create_public_session

            public_session = get_or_create_public_session(
                request,
                page_type=page_type,
                country=country,
                language=language,
            )
        except Exception:
            logger.exception(
                "public_analytics: error resolving session path=%s",
                getattr(request, "path", ""),
            )

        now = timezone.now()
        visitor_hash = PublicPageView.build_visitor_hash(
            ip=ip,
            user_agent=user_agent,
            date_key=now.date().isoformat(),
        )

        is_non_human = is_probable_non_human_request(request, user_agent)
        page_view = PublicPageView.objects.create(
            path=request.path[:255],
            host=host[:255],
            page_type=page_type,
            country=(country or "").lower()[:8],
            language=(language or "").lower()[:8],
            visitor_hash=visitor_hash,
            public_session=public_session,
            referrer=_clean_referrer(request),
            user_agent=user_agent,
            is_mobile=_is_mobile(user_agent),
            is_bot=is_probable_bot(user_agent) or is_non_human,
            is_internal=bool(public_session and public_session.is_internal),
            created_at=now,
        )
        if (
            public_session
            and not public_session.is_bot
            and not public_session.is_internal
            and is_canonical_public_host(host)
        ):
            try:
                from taller.models.public_analytics_event import PublicAnalyticsEvent
                from taller.services.public_event_tracking import record_public_event

                record_public_event(
                    session=public_session,
                    event_type=PublicAnalyticsEvent.EVENT_HUMAN_VISIT,
                    path=page_view.path,
                    dedupe_key="human_visit",
                    metadata={"source": "backend"},
                    page_view=page_view,
                )
            except Exception:
                logger.exception(
                    "public_analytics: error tracking human visit path=%s",
                    getattr(request, "path", ""),
                )
        return page_view
    except Exception:
        logger.exception(
            "public_analytics: error tracking path=%s",
            getattr(request, "path", ""),
        )
        return None
