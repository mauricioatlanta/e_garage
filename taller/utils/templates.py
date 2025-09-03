from django.template.loader import select_template, get_template
from django.template import TemplateDoesNotExist

def country_lang_template(path: str, country: str, lang: str):
    """
    Selecciona template basado en país e idioma con fallbacks usando la nueva estructura canónica.
    
    Args:
        path: Ruta del template (ej: "clientes/crear_cliente.html")
        country: Código de país (cl/us)
        lang: Código de idioma (es/en)
    
    Returns:
        Template seleccionado usando la jerarquía:
        1. {country}/{lang}/{path}
        2. {country}/{fallback_lang}/{path} (si country=us y lang=en, fallback a es)
        3. common/{path}
    """
    country = (country or "cl").lower()
    lang = (lang or "es").lower()
    
    candidates = []
    
    # Template específico del país e idioma
    if country and lang:
        candidates.append(f"{country}/{lang}/{path}")
        
        # Fallback dentro del país (solo para USA inglés → español)
        if country == "us" and lang == "en":
            candidates.append(f"{country}/es/{path}")
    
    # Fallback global
    candidates.append(f"common/{path}")
    
    return select_template(candidates)

def get_country_from_request(request):
    """
    Obtiene el país desde el request, con prioridad:
    1. request.country (seteado por CountryContextMiddleware)
    2. URL path (/cl/ o /us/)
    3. Usuario/empresa
    """
    # Prioridad 1: País detectado por middleware
    if hasattr(request, 'country') and request.country:
        return request.country.lower()
    
    # Prioridad 2: País desde URL
    path = request.path.lower()
    if path.startswith('/cl/'):
        return 'cl'
    elif path.startswith('/us/'):
        return 'us'
    
    # Prioridad 3: País del usuario/empresa
    if hasattr(request, 'user') and request.user.is_authenticated:
        if hasattr(request.user, 'empresa') and hasattr(request.user.empresa, 'pais'):
            return request.user.empresa.pais.lower()
    
    return None

def select_country_lang_template(base_path: str, country: str, lang: str, fallback_lang="es"):
    """
    Función legacy mantenida para compatibilidad.
    Devuelve la ruta del template como cadena, no el objeto Template.
    """
    # Construir la ruta del template directamente
    country = (country or "cl").lower()
    lang = (lang or "es").lower()
    
    # Construir candidatos en orden de prioridad
    candidates = []
    
    # Template específico del país e idioma
    if country and lang:
        candidates.append(f"{country}/{lang}/{base_path}")
        
        # Fallback dentro del país (solo para USA inglés → español)
        if country == "us" and lang == "en":
            candidates.append(f"{country}/es/{base_path}")
    
    # Fallback global
    candidates.append(f"common/{base_path}")
    
    # Devolver la primera ruta que exista
    from django.template.loader import get_template
    for candidate in candidates:
        try:
            get_template(candidate)
            return candidate
        except:
            continue
    
    # Si no se encuentra ninguno, devolver el fallback común
    return f"common/{base_path}"
