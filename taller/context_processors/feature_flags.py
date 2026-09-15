"""
Context processor: expone country_features y country_code.
Prioridad: request.country → request.user.empresa.pais → CL.
"""

from taller.config.feature_flags import get_country_features
from taller.services.empresa_service import get_empresa_safe


def country_features(request):
    """Inyecta country_features y country_code en el contexto de templates."""
    country = getattr(request, "country", None)
    if (
        not country
        and getattr(request, "user", None)
        and getattr(request.user, "is_authenticated", False)
    ):
        try:
            empresa = get_empresa_safe(request)
            if empresa:
                country = getattr(empresa, "pais", None)
        except Exception:
            pass
    if not country:
        country = "CL"
    code = (country or "CL").upper() if isinstance(country, str) else "CL"
    features = get_country_features(code)
    return {
        "country_features": features,
        "country_code": features["country"],
    }
