"""
Vista custom para fallos CSRF: loguea la razón exacta (token, referer, origin).
Uso temporal en producción para confirmar si el 403 en POST login es CSRF.

En settings (temporal):
    CSRF_FAILURE_VIEW = "taller.views_extra.csrf_debug.csrf_failure"
"""

import logging

from django.http import HttpResponseForbidden

logger = logging.getLogger(__name__)


def csrf_failure(request, reason=""):
    referer = request.headers.get("referer", "")
    origin = request.headers.get("origin", "")
    logger.warning(
        "CSRF failure on %s %s | reason=%s | referer=%s | origin=%s",
        request.method,
        request.path,
        reason,
        referer,
        origin,
    )
    return HttpResponseForbidden(f"CSRF failure: {reason}")
