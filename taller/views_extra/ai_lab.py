"""
Compat stub: AI Lab dashboard. Temporal hasta restaurar vista real.
"""

from django.shortcuts import redirect


def ai_lab_dashboard(request, *args, **kwargs):
    """Stub: redirige al dashboard principal."""
    return redirect("taller:dashboard")
