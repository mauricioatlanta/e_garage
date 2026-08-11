import logging
from urllib.parse import urlparse

from django.utils import timezone

from taller.models.public_page_view import PublicPageView, is_probable_bot
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
        ip = get_client_ip(request) or ""

        now = timezone.now()
        visitor_hash = PublicPageView.build_visitor_hash(
            ip=ip,
            user_agent=user_agent,
            date_key=now.date().isoformat(),
        )

        return PublicPageView.objects.create(
            path=request.path[:255],
            page_type=page_type,
            country=(country or "").lower()[:8],
            language=(language or "").lower()[:8],
            visitor_hash=visitor_hash,
            referrer=_clean_referrer(request),
            user_agent=user_agent,
            is_mobile=_is_mobile(user_agent),
            is_bot=is_probable_bot(user_agent),
            created_at=now,
        )
    except Exception:
        logger.exception(
            "public_analytics: error tracking path=%s",
            getattr(request, "path", ""),
        )
        return None
