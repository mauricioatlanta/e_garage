"""Trust & Security signals — Phase 1."""

import logging

from django.contrib.auth.signals import user_logged_out
from django.db.models import F
from django.dispatch import receiver
from django.utils import timezone

logger = logging.getLogger("egarage.auth")

_TRUST_SESSION_KEY = "_trust"


@receiver(user_logged_out)
def on_user_logout(sender, request, user, **kwargs):
    """
    On logout: flush any pending page counts and mark the session as inactive.
    Reads _trust.pending from the Django session so no page views are lost
    even when logout happens before the 60-second write interval fires.
    """
    if request is None or user is None:
        return
    session_key = getattr(request.session, "session_key", None)
    if not session_key:
        return

    try:
        from taller.models.sesion_usuario import SesionUsuario

        trust_data = request.session.get(_TRUST_SESSION_KEY, {})
        pending = trust_data.get("pending", 0)

        update_kwargs = {"activa": False, "ultima_actividad": timezone.now()}
        if pending > 0:
            update_kwargs["paginas_visitadas"] = F("paginas_visitadas") + pending

        SesionUsuario.objects.filter(session_key=session_key).update(**update_kwargs)
    except Exception as exc:
        logger.warning("trust: error flushing session on logout: %s", exc)
