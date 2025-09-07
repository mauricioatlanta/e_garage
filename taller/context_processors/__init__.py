"""Paquete de context processors de ``taller``.

Soluciona conflicto entre un archivo ``context_processors.py`` y este
paquete homónimo que impedía que Django resolviera rutas como
``taller.context_processors.empresa_contexto``. Ahora las funciones se
exponen directamente desde el paquete para que ``import_string`` de
Django obtenga el callable correcto.
"""

from django.core.cache import cache

from .company_header import company_header  # ✅ NUEVO - Información de contacto

# Traer la función existente definida en submódulo independiente
from .empresa_contexto import empresa_contexto as _empresa_contexto_impl
from .namespaces import ui_namespaces  # útil para otros settings


def company_context(request):
    """Context processor para datos de empresa y configuración estática."""
    empresa = (
        getattr(request.user, "empresa", None)
        if hasattr(request, "user") and request.user.is_authenticated
        else None
    )
    country = getattr(empresa, "pais", "CL") if empresa else "CL"
    company_settings = getattr(empresa, "configuracion", None) if empresa else None
    return {
        "country": country,
        "company_settings": company_settings,
        "STATIC_VERSION": "dev",
        "company": getattr(request, "company", None),
    }


def empresa_contexto(request):  # noqa: D401
    """Wrapper que delega en la implementación importada.

    Se define aquí para que el atributo exista en el paquete y Django
    pueda encontrarlo con la ruta acortada utilizada en settings.
    """
    return _empresa_contexto_impl(request)


def company_branding(request):
    """Inyecta configuración extendida de branding.

    Usa caché por usuario para reducir consultas.
    Importa el modelo de forma perezosa para evitar ciclos.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {
            "company_settings": None,
            "company_name": "eGarage",
            "company_logo": "/static/images/egarage_default_logo.png",
            "company_logo_url": "/static/images/egarage_default_logo.png",
            "primary_color": "#0d6efd",
            "secondary_color": "#6c757d",
        }

    from taller.models import ConfiguracionEmpresa
    from taller.models.empresa import Empresa

    cache_key = f"company_branding_{user.id}"
    cached_data = cache.get(cache_key)

    if cached_data is None:
        try:
            # Buscar empresa del usuario
            empresa = None
            try:
                empresa = Empresa.objects.get(user=user)
            except Empresa.DoesNotExist:
                try:
                    empresa = Empresa.objects.filter(usuario=user).first()
                except:
                    pass

            company_settings = None
            if empresa:
                try:
                    company_settings = empresa.config
                except ConfiguracionEmpresa.DoesNotExist:
                    pass

            # Determinar logo URL
            logo_url = "/static/images/egarage_default_logo.png"
            if company_settings and company_settings.logo:
                logo_url = company_settings.logo.url

            # Determinar nombre de empresa
            company_name = "eGarage"
            if company_settings and company_settings.nombre_publico:
                company_name = company_settings.nombre_publico
            elif empresa:
                company_name = empresa.nombre_taller

            cached_data = {
                "company_settings": company_settings,
                "company_name": company_name,
                "company_logo": logo_url,
                "company_logo_url": logo_url,
                "primary_color": (
                    company_settings.brand_color
                    if company_settings and company_settings.brand_color
                    else "#0d6efd"
                ),
                "secondary_color": "#6c757d",
            }

            if company_settings:
                cached_data.update(
                    {
                        "company_tagline": company_settings.tagline,
                        "company_currency": company_settings.moneda,
                    }
                )

            cache.set(cache_key, cached_data, 3600)
        except Exception as e:
            print(f"Error en company_branding: {e}")
            cache.set(cache_key, "error", 600)
            cached_data = {
                "company_settings": None,
                "company_name": "eGarage",
                "company_logo": "/static/images/egarage_default_logo.png",
                "company_logo_url": "/static/images/egarage_default_logo.png",
                "primary_color": "#0d6efd",
                "secondary_color": "#6c757d",
            }

    if cached_data == "error":
        cached_data = {
            "company_settings": None,
            "company_name": "eGarage",
            "company_logo": "/static/images/egarage_default_logo.png",
            "company_logo_url": "/static/images/egarage_default_logo.png",
            "primary_color": "#0d6efd",
            "secondary_color": "#6c757d",
        }

    return cached_data


def company_country(request):
    """Inyecta información de país de la empresa."""
    from taller.models.empresa import Empresa

    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"company_country": "CL"}

    try:
        empresa = Empresa.objects.get(user=user)
        return {"company_country": empresa.pais}
    except Empresa.DoesNotExist:
        return {"company_country": "CL"}


def invalidate_company_cache(user):
    """Invalida el caché de branding para un usuario específico.

    Args:
            user: Puede ser un objeto User o un ID de usuario (int)
    """
    if hasattr(user, "id"):
        user_id = user.id
    else:
        user_id = user  # Es un ID directamente

    cache_key = f"company_branding_{user_id}"
    cache.delete(cache_key)


__all__ = [
    "empresa_contexto",
    "company_branding",
    "company_country",
    "company_context",
    "company_header",  # ✅ NUEVO - Información de contacto
    "invalidate_company_cache",
    "ui_namespaces",
]
