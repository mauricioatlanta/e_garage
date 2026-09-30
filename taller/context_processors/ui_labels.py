# taller/context_processors/ui_labels.py

from taller.config.ui_labels import get_document_module_label, get_ui_labels
from taller.services.empresa_service import get_empresa_safe


# Mapa entre prefijos de URL y códigos de país usados en el sistema
URL_PREFIX_TO_COUNTRY = {
    "cl": "CL",
    "us": "US",
    "mx": "MX",
    "pe": "PE",
    "co": "CO",
    "ar": "AR",
    "br": "BR",
    "ec": "EC",
    "ve": "VE",
    "uy": "UY",
}


def _get_country_from_path(path):
    """
    Dado un path como '/cl/es/documentos/lista/',
    retorna el código de país en MAYÚSCULA (por ejemplo 'CL').

    Si no se puede determinar, usa CL por defecto.
    """
    if not path:
        return "CL"

    # Quita slashes iniciales/finales y toma el primer segmento
    parts = path.strip("/").split("/")
    if not parts:
        return "CL"

    prefix = parts[0].lower()
    return URL_PREFIX_TO_COUNTRY.get(prefix, "CL")


def ui_labels_context(request):
    """
    Context processor que inyecta 'ui_labels' en todas las plantillas.

    Usa:
    - el prefijo de la URL para inferir el país (cl, us, mx, etc.)
    - request.LANGUAGE_CODE (si está disponible) para el idioma
    """
    path = request.path or "/"
    active_empresa = getattr(request, "empresa", None) or get_empresa_safe(request)
    if active_empresa:
        country_code = str(getattr(active_empresa, "pais", "") or "").strip().upper() or "CL"
    else:
        country_code = _get_country_from_path(path)

    language_code = getattr(request, "LANGUAGE_CODE", None)
    labels = dict(get_ui_labels(country_code=country_code, language_code=language_code))
    is_english = str(language_code or "").lower().startswith("en")
    labels.setdefault("workflow_singular", "Document" if is_english else "Documento")

    active_config = getattr(active_empresa, "config", None) if active_empresa else None
    rubro = getattr(active_config, "rubro_principal", None)
    if rubro:
        module_label = get_document_module_label(rubro, language_code)
        labels["documents_menu"] = module_label
        labels["document_center"] = module_label
        if module_label in {"Work", "Trabajos"}:
            labels["workflow_singular"] = "Work" if is_english else "Trabajo"
            labels["new_document"] = "New Work" if is_english else "Nuevo Trabajo"
            labels["create_button"] = "Create Work" if is_english else "Crear Trabajo"
            labels["edit_button"] = "Edit Work" if is_english else "Editar Trabajo"
        elif module_label in {"Sales", "Ventas"}:
            labels["workflow_singular"] = "Sale" if is_english else "Venta"
            labels["new_document"] = "New Sale" if is_english else "Nueva Venta"
            labels["create_button"] = "Create Sale" if is_english else "Crear Venta"
            labels["edit_button"] = "Edit Sale" if is_english else "Editar Venta"
        else:
            labels["workflow_singular"] = "Document" if is_english else "Documento"

    return {
        "ui_labels": labels,
        "ui_country_code": country_code,
    }
