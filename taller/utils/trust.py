"""
Trust & Security — Phase 1 detection utilities.

Functions here operate on SesionUsuario data and are intentionally
import-free of Django ORM at module level so they can be unit-tested
without database setup.
"""
from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from django.utils import timezone

if TYPE_CHECKING:
    from django.contrib.auth.models import User


INACTIVITY_MINUTES = 30
CONCURRENT_WINDOW_MINUTES = 15
HIGH_PAGE_COUNT = 200


def mark_inactive_sessions() -> int:
    """Mark sessions with no activity in the last INACTIVITY_MINUTES as inactive."""
    from taller.models.sesion_usuario import SesionUsuario

    cutoff = timezone.now() - timedelta(minutes=INACTIVITY_MINUTES)
    return SesionUsuario.objects.filter(activa=True, ultima_actividad__lt=cutoff).update(
        activa=False
    )


def get_concurrent_sessions(usuario, window_minutes: int = CONCURRENT_WINDOW_MINUTES):
    """Return active sessions for user within the time window."""
    from taller.models.sesion_usuario import SesionUsuario

    cutoff = timezone.now() - timedelta(minutes=window_minutes)
    return SesionUsuario.objects.filter(
        usuario=usuario, activa=True, ultima_actividad__gte=cutoff
    ).exclude(paginas_visitadas=0)


def detect_shared_account(usuario) -> dict | None:
    """
    Return a flag dict if the account shows signs of concurrent sharing,
    None otherwise.

    Signs detected (server-side only, no JS):
    - 2+ active sessions with distinct device fingerprints
    - 2+ active sessions with distinct countries
    """
    sessions = list(get_concurrent_sessions(usuario).values("device_fingerprint", "ip", "pais"))
    if len(sessions) < 2:
        return None

    fingerprints = {s["device_fingerprint"] for s in sessions}
    countries = {s["pais"] for s in sessions if s["pais"]}

    if len(fingerprints) > 1:
        return {
            "type": "shared_account",
            "reason": "concurrent_devices",
            "distinct_fingerprints": len(fingerprints),
            "distinct_countries": len(countries),
            "session_count": len(sessions),
        }

    if len(countries) > 1:
        return {
            "type": "shared_account",
            "reason": "concurrent_countries",
            "distinct_countries": len(countries),
            "session_count": len(sessions),
        }

    return None


def detect_high_navigation(usuario) -> dict | None:
    """Flag sessions with unusually high page counts in the last 24h."""
    from django.db.models import Sum

    from taller.models.sesion_usuario import SesionUsuario

    cutoff = timezone.now() - timedelta(hours=24)
    total = (
        SesionUsuario.objects.filter(usuario=usuario, inicio_sesion__gte=cutoff).aggregate(
            total=Sum("paginas_visitadas")
        )["total"]
        or 0
    )
    if total >= HIGH_PAGE_COUNT:
        return {"type": "high_navigation", "pages_24h": total, "threshold": HIGH_PAGE_COUNT}
    return None
