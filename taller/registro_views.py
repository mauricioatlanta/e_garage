"""
⚠️ DEPRECATED: Este archivo contiene código legacy de registro unificado.

El sistema de registro ha sido refactorizado para usar RegistrationService unificado.
Todas las funcionalidades de registro ahora están en:
- taller/views_extra/suscripcion.py (registro con planes)
- scripts/onboarding_views.py (registro gratuito API)
- taller/views_extra/custom_signup.py (registro Allauth)

Este archivo se mantiene solo para compatibilidad con URLs legacy.
"""

from django.http import HttpResponsePermanentRedirect


def registro_unificado(request):
    """
    ⚠️ DEPRECATED: Redirige permanentemente al flujo moderno de registro.

    El registro unificado ha sido reemplazado por:
    - /registro/ (registro con planes)
    - /registro-gratuito/ (registro gratuito API)
    - /accounts/signup/ (registro Allauth)
    """
    # Redirigir permanentemente (301) al flujo moderno
    return HttpResponsePermanentRedirect("/registro/")
