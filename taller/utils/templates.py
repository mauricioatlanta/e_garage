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

def select_country_lang_template(base_path: str, country: str, lang: str, fallback_lang="es"):
    """
    Función legacy mantenida para compatibilidad.
    Usa la nueva función country_lang_template internamente.
    """
    return country_lang_template(base_path, country, lang)
