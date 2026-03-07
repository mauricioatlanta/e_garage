from django.template import TemplateDoesNotExist
from django.template.loader import get_template


def select_country_lang_template(base_path: str, country: str, lang: str, fallback_lang="es"):
    """
    Arquitectura híbrida (Opción C):
    1) taller/{country}/{lang}/{base_path}
    2) taller/{country}/{lang}/common/{base_path}
    3) taller/{country}/common/{base_path}
    4) taller/common/{base_path}

    US nunca cae a CL. Lista para escalar a MX, PE, BR.
    """
    country = (country or "CL").lower()
    lang = (lang or fallback_lang).lower()
    fallback_lang = (fallback_lang or "es").lower()

    # Idiomas a intentar dentro del mismo país (sin duplicados)
    langs = []
    for code in [lang, fallback_lang]:
        if code and code not in langs:
            langs.append(code)

    if country == "us":
        for code in ["en", "es"]:
            if code not in langs:
                langs.append(code)

    candidates = []

    # 1) País + idioma (y common por idioma)
    for l in langs:
        candidates += [
            f"taller/{country}/{l}/{base_path}",
            f"taller/{country}/{l}/common/{base_path}",
        ]

    # 2) País common (sin idioma)
    candidates += [
        f"taller/{country}/common/{base_path}",
    ]

    # 3) Global common
    candidates += [
        f"taller/common/{base_path}",
    ]

    for candidate in candidates:
        try:
            get_template(candidate)
            return candidate
        except TemplateDoesNotExist:
            continue

    # Último recurso (muy raro): devolver global common igualmente
    return f"taller/common/{base_path}"
