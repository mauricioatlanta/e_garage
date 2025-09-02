from django.conf import settings
from django.core.cache import cache


def company_branding_context(request):
    """
    Context processor global para inyectar información de empresa en todas las plantillas.
    Proporciona company_name y company_logo_url de forma consistente.
    """
    # DEBUG: Agregar logging temporal
    print(f"🔍 DEBUG: Context processor llamado para usuario: {getattr(request, 'user', None)}")
    print(f"🔍 DEBUG: Context processor EJECUTÁNDOSE - INICIO")
    
    # No aplicar en rutas sin usuario
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        print(f"🔍 DEBUG: Usuario no autenticado, retornando vacío")
        return {}

    empresa = getattr(user, "empresa", None)
    if not empresa:
        print(f"🔍 DEBUG: Usuario sin empresa, retornando vacío")
        return {}

    # Usa cache leve por request.user.empresa_id y país para performance
    country = getattr(request, "country", None) or getattr(request, "COUNTRY", None) or "NA"
    cache_key = f"ctx_company:{empresa.id}:{country}"
    
    print(f"🔍 DEBUG: Cache key: {cache_key}")
    
    data = cache.get(cache_key)
    if data:
        print(f"🔍 DEBUG: Cache hit, retornando: {data}")
        return data

    print(f"🔍 DEBUG: Cache miss, calculando datos...")

    # Origen de verdad: ConfiguracionEmpresa (modelo legacy que se usa actualmente)
    company_name = ""
    logo_url = ""
    tagline = ""

    try:
        # Intentar obtener configuración de empresa
        configuracion = getattr(empresa, "config", None)
        if configuracion:
            # Usar nombre_publico si existe, sino usar nombre_taller de empresa
            company_name = getattr(configuracion, "nombre_publico", "") or getattr(empresa, "nombre_taller", "")
            
            # Obtener tagline
            tagline = getattr(configuracion, "tagline", "") or ""
            
            # Obtener URL del logo
            logo_field = getattr(configuracion, "logo", None)
            if logo_field and hasattr(logo_field, "url"):
                try:
                    logo_url = logo_field.url
                except (ValueError, AttributeError):
                    logo_url = ""
        else:
            # Fallback: usar datos directos de empresa
            company_name = getattr(empresa, "nombre_taller", "")
            tagline = ""
            logo_field = getattr(empresa, "logo", None)
            if logo_field and hasattr(logo_field, "url"):
                try:
                    logo_url = logo_field.url
                except (ValueError, AttributeError):
                    logo_url = ""
                    
    except Exception as e:
        print(f"🔍 DEBUG: Error obteniendo datos: {e}")
        # Fallback en caso de error
        company_name = getattr(empresa, "nombre_taller", "")
        tagline = ""
        logo_url = ""

    # Preparar datos para cache
    data = {
        "company_name": company_name or "eGarage",
        "company_logo_url": logo_url,
        "company_tagline": tagline,
    }
    
    print(f"🔍 DEBUG: Datos calculados: {data}")
    print(f"🔍 DEBUG: company_name final: '{data['company_name']}'")
    print(f"🔍 DEBUG: company_tagline final: '{data['company_tagline']}'")
    print(f"🔍 DEBUG: company_logo_url final: '{data['company_logo_url']}'")
    print(f"🔍 DEBUG: Context processor EJECUTÁNDOSE - FIN")
    
    # Cache por 60 segundos
    cache.set(cache_key, data, 60)
    return data


def invalidate_company_branding_cache(empresa_id, request=None):
    """
    Invalida el cache del context processor para una empresa específica.
    Llamar después de actualizar nombre o logo de empresa.
    """
    # Invalidar para todos los países conocidos
    countries = ["CL", "US", "NA"]
    for country in countries:
        cache_key = f"ctx_company:{empresa_id}:{country}"
        cache.delete(cache_key)
        print(f"🔍 DEBUG: Cache invalidado: {cache_key}")