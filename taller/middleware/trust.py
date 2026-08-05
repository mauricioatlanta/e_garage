"""
Trust & Security middleware — Phase 1.

Tracks one SesionUsuario row per Django session for authenticated users.
Skips static/media assets and unauthenticated requests.

Write throttling: DB is updated at most every WRITE_INTERVAL_SECONDS (default 60s)
to avoid one UPDATE per page view. Counters are batched in the Django session and
flushed on interval, so page counts remain accurate.
"""

import logging
import time

from django.db.models import F
from django.utils import timezone

from taller.utils.smart_logging import get_client_ip

logger = logging.getLogger("egarage.auth")

_SKIP_PREFIXES = (
    "/static/",
    "/media/",
    "/favicon",
    "/__debug__/",
)

WRITE_INTERVAL_SECONDS = 60
_TRUST_SESSION_KEY = "_trust"


def _should_skip(path: str) -> bool:
    return any(path.startswith(p) for p in _SKIP_PREFIXES)


class TrustMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not request.user.is_authenticated or _should_skip(request.path):
            return response

        session_key = request.session.session_key
        if not session_key:
            return response

        try:
            self._track(request, session_key)
        except Exception as exc:
            logger.warning("trust: session tracking error: %s", exc)

        return response

    def _track(self, request, session_key: str) -> None:
        from taller.models.sesion_usuario import SesionUsuario
        from taller.utils.trust import detect_shared_account

        ip = get_client_ip(request)
        ua_raw = request.META.get("HTTP_USER_AGENT", "")[:500]
        accept_lang = request.META.get("HTTP_ACCEPT_LANGUAGE", "")[:100]
        accept_enc = request.META.get("HTTP_ACCEPT_ENCODING", "")[:100]
        fingerprint = SesionUsuario.build_fingerprint(ua_raw, accept_lang, accept_enc)
        pais = getattr(request, "country", "") or ""
        empresa = getattr(request, "empresa", None)

        sesion = SesionUsuario.objects.filter(session_key=session_key).first()

        if sesion is None:
            # First page of a new session counts as 1
            parsed = SesionUsuario.parse_ua(ua_raw)
            sesion = SesionUsuario.objects.create(
                usuario=request.user,
                empresa=empresa,
                session_key=session_key,
                device_fingerprint=fingerprint,
                ip=ip,
                pais=pais,
                user_agent=ua_raw,
                navegador=parsed["navegador"],
                os=parsed["os"],
                es_mobile=parsed["es_mobile"],
                paginas_visitadas=1,
                activa=True,
            )
            request.session[_TRUST_SESSION_KEY] = {"pending": 0, "last_flush": time.time()}
            return

        # Accumulate page count in the Django session (no DB write per page)
        trust_data = request.session.get(_TRUST_SESSION_KEY, {"pending": 0, "last_flush": 0})
        trust_data["pending"] += 1
        now_ts = time.time()
        elapsed = now_ts - trust_data.get("last_flush", 0)

        if elapsed >= WRITE_INTERVAL_SECONDS:
            pending = trust_data["pending"]
            update_kwargs = {
                "paginas_visitadas": F("paginas_visitadas") + pending,
                "ultima_actividad": timezone.now(),
                "activa": True,
            }
            if empresa:
                update_kwargs["empresa"] = empresa
            SesionUsuario.objects.filter(pk=sesion.pk).update(**update_kwargs)

            trust_data = {"pending": 0, "last_flush": now_ts}

            # Phase 2 hook: check for shared-account signals after each flush
            sesion.refresh_from_db(fields=["paginas_visitadas", "flags"])
            flag = detect_shared_account(request.user)
            if flag and flag != sesion.flags.get("shared_account"):
                sesion.flags["shared_account"] = flag
                sesion.save(update_fields=["flags"])

        request.session[_TRUST_SESSION_KEY] = trust_data
