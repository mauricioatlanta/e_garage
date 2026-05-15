import logging

from django.conf import settings
from django.contrib.sessions.exceptions import SessionInterrupted
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponseRedirect
from django.shortcuts import resolve_url
from django.utils.cache import patch_vary_headers

logger = logging.getLogger(__name__)


class SafeSessionMiddleware(SessionMiddleware):
    """
    Convert concurrent session deletion races into a normal response.

    Django raises SessionInterrupted when another request deletes the same
    session before process_response() can save it. For logout races, the right
    fallback is to drop the stale cookie instead of returning a 500.
    """

    def __call__(self, request):
        try:
            return super().__call__(request)
        except SessionInterrupted:
            logger.warning(
                "Suppressed SessionInterrupted from downstream middleware",
                extra={
                    "path": getattr(request, "path", ""),
                    "method": getattr(request, "method", ""),
                },
            )
            response = HttpResponseRedirect(resolve_url(getattr(settings, "LOGIN_URL", "/") or "/"))
            self._clear_session_cookie(request, response)
            return response

    def process_response(self, request, response):
        try:
            return super().process_response(request, response)
        except SessionInterrupted:
            logger.info(
                "Suppressed SessionInterrupted during response processing",
                extra={
                    "path": getattr(request, "path", ""),
                    "method": getattr(request, "method", ""),
                },
            )
            self._clear_session_cookie(request, response)
            return response

    @staticmethod
    def _clear_session_cookie(request, response):
        if settings.SESSION_COOKIE_NAME in getattr(request, "COOKIES", {}):
            response.delete_cookie(
                settings.SESSION_COOKIE_NAME,
                path=settings.SESSION_COOKIE_PATH,
                domain=settings.SESSION_COOKIE_DOMAIN,
                samesite=settings.SESSION_COOKIE_SAMESITE,
            )
            patch_vary_headers(response, ("Cookie",))
