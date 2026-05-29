from django.template import TemplateDoesNotExist
from django.template.loader import get_template


def select_country_lang_template(base_path: str, country: str, lang: str, fallback_lang="es"):
    """
    Selecciona template basado en país e idioma con fallbacks.

    Args:
        base_path: Ruta base del template (ej: "documentos/crear_documento.html")
        country: Código de país (CL/US)
        lang: Código de idioma (es/en)
        fallback_lang: Idioma de fallback por defecto

    Returns:
        Nombre del template seleccionado usando la jerarquía:
        1. taller/{country}/{lang}/{base_path}
        2. taller/{country}/{lang}/common/{base_path}
        3. taller/{country}/{fallback_lang}/{base_path}
        4. taller/{country}/{fallback_lang}/common/{base_path}
        5. taller/{country}/{base_path}  (ej. taller/us/documentos/... para USA)
        6. taller/cl/{lang}/{base_path}
        7. taller/cl/{lang}/common/{base_path}
        8. taller/common/{base_path}
    """
    country = (country or "CL").lower()
    lang = (lang or fallback_lang).lower()

    candidates = [
        f"taller/{country}/{lang}/{base_path}",
        f"taller/{country}/{lang}/common/{base_path}",
        f"taller/{country}/{fallback_lang}/{base_path}",
        f"taller/{country}/{fallback_lang}/common/{base_path}",
        f"taller/{country}/{base_path}",
        f"taller/cl/{lang}/{base_path}",
        f"taller/cl/{lang}/common/{base_path}",
        f"taller/common/{base_path}",
    ]

    # Intentar encontrar el primer template que existe
    for candidate in candidates:
        try:
            get_template(candidate)
            return candidate
        except TemplateDoesNotExist:
            continue

    # Si ninguno existe, retornar el último candidato como fallback
    return candidates[-1]
