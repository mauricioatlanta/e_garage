# taller/config/ui_labels.py

"""
Diccionario maestro de labels por país/idioma para el módulo de Documentos/Invoicing.

NOTA IMPORTANTE:
- No toca el modelo Documento.
- Solo define textos para el frontend (menus, botones, títulos, etc.).
- Las claves internas (ej: 'document_type_invoice') son genéricas.
- Los valores dependen del país/idioma.
"""

from django.conf import settings


# ---------------------------
# USA - Inglés
# ---------------------------
UI_LABELS_US_EN = {
    "documents_menu": "Documents",
    "new_document": "New Document",
    "document_center": "Documents",
    "document_type_invoice": "Invoice",
    "document_type_estimate": "Estimate",
    "document_type_work_order": "Work Order",
    "document_number": "Invoice Number",
    "create_button": "Create Document",
    "edit_button": "Edit Document",
}


# ---------------------------
# Chile - Español
# ---------------------------
UI_LABELS_CL_ES = {
    "documents_menu": "Documentos",
    "new_document": "Nuevo Documento",
    "document_center": "Documentos",
    "document_type_invoice": "Comprobante",
    "document_type_estimate": "Presupuesto",
    "document_type_work_order": "Orden de Trabajo",
    "document_number": "N° Documento",
    "create_button": "Crear Documento",
    "edit_button": "Editar Documento",
}


# ---------------------------
# México - Español
# ---------------------------
UI_LABELS_MX_ES = {
    "documents_menu": "Documentos",
    "new_document": "Nuevo Documento",
    "document_center": "Documentos",
    "document_type_invoice": "Comprobante",
    "document_type_estimate": "Cotización",
    "document_type_work_order": "Orden de Servicio",
    "document_number": "Folio",
    "create_button": "Crear Documento",
    "edit_button": "Editar Documento",
}


# ---------------------------
# Perú - Español
# ---------------------------
UI_LABELS_PE_ES = {
    "documents_menu": "Comprobantes",
    "new_document": "Nuevo Comprobante",
    "document_center": "Comprobantes",
    "document_type_invoice": "Comprobante",
    "document_type_estimate": "Proforma",
    "document_type_work_order": "Orden de Servicio",
    "document_number": "N° Comprobante",
    "create_button": "Crear Comprobante",
    "edit_button": "Editar Comprobante",
}


# ---------------------------
# Colombia - Español
# ---------------------------
UI_LABELS_CO_ES = {
    "documents_menu": "Documentos",
    "new_document": "Nuevo Documento",
    "document_center": "Documentos",
    "document_type_invoice": "Comprobante",
    "document_type_estimate": "Cotización",
    "document_type_work_order": "Orden de Trabajo",
    "document_number": "N° Documento",
    "create_button": "Crear Documento",
    "edit_button": "Editar Documento",
}


# ---------------------------
# Argentina - Español
# ---------------------------
UI_LABELS_AR_ES = {
    "documents_menu": "Comprobantes",
    "new_document": "Nuevo Comprobante",
    "document_center": "Comprobantes",
    "document_type_invoice": "Comprobante",
    "document_type_estimate": "Presupuesto",
    "document_type_work_order": "Orden de Trabajo",
    "document_number": "N° Comprobante",
    "create_button": "Crear Comprobante",
    "edit_button": "Editar Comprobante",
}


# ---------------------------
# Brasil - Portugués
# ---------------------------
UI_LABELS_BR_PT = {
    "documents_menu": "Documentos",
    "new_document": "Novo Documento",
    "document_center": "Documentos",
    "document_type_invoice": "Nota Fiscal",
    "document_type_estimate": "Orçamento",
    "document_type_work_order": "Ordem de Serviço",
    "document_number": "Número do Documento",
    "create_button": "Criar Documento",
    "edit_button": "Editar Documento",
}


# ---------------------------
# Ecuador - Español
# ---------------------------
UI_LABELS_EC_ES = {
    "documents_menu": "Comprobantes",
    "new_document": "Nuevo Comprobante",
    "document_center": "Comprobantes",
    "document_type_invoice": "Comprobante",
    "document_type_estimate": "Proforma",
    "document_type_work_order": "Orden de Trabajo",
    "document_number": "N° Comprobante",
    "create_button": "Crear Comprobante",
    "edit_button": "Editar Comprobante",
}


# ---------------------------
# Venezuela - Español
# ---------------------------
UI_LABELS_VE_ES = {
    "documents_menu": "Documentos",
    "new_document": "Nuevo Documento",
    "document_center": "Documentos",
    "document_type_invoice": "Comprobante",
    "document_type_estimate": "Presupuesto",
    "document_type_work_order": "Orden de Servicio",
    "document_number": "N° Control",
    "create_button": "Crear Documento",
    "edit_button": "Editar Documento",
}


# ---------------------------
# Uruguay - Español
# ---------------------------
UI_LABELS_UY_ES = {
    "documents_menu": "Comprobantes",
    "new_document": "Nuevo Comprobante",
    "document_center": "Comprobantes",
    "document_type_invoice": "Comprobante",
    "document_type_estimate": "Presupuesto",
    "document_type_work_order": "Orden de Trabajo",
    "document_number": "N° Comprobante",
    "create_button": "Crear Comprobante",
    "edit_button": "Editar Comprobante",
}


# ---------------------------
# Helper principal
# ---------------------------

# Desde settings (EGARAGE_DEFAULT_*) para una sola fuente de verdad; fallback Chile/es
DEFAULT_COUNTRY_CODE = getattr(settings, "EGARAGE_DEFAULT_COUNTRY", "cl").upper()
DEFAULT_LANGUAGE_CODE = getattr(settings, "EGARAGE_DEFAULT_LANG", "es")


WORK_LABEL_RUBROS = {
    "WORKSHOP",
    "WORKSHOP_MOTO",
    "WORKSHOP_HEAVY",
    "EXHAUST",
    "BODYSHOP",
    "ELECTRIC",
    "GLASS_AUDIO",
    "FLEET",
    "FLEET_REPAIR",
    "DETAILING",
    "SUSPENSION_STEERING",
    "BRAKES",
    "OBD_DIAGNOSTIC",
    "CLASSIC_CARS",
    "AUDIO_ENTERTAINMENT",
    "GAS_CONVERSION",
    "BODY_GLASS",
    "TUNING",
}


def get_document_module_label(rubro, language_code=None):
    """Return the business-facing name for the document workflow button."""
    rubro = str(rubro or "WORKSHOP").strip().upper()
    language_code = str(language_code or DEFAULT_LANGUAGE_CODE).lower()

    if rubro in {"PARTS", "DESARMADURIA", "MIXED", "TIRE"}:
        return "Sales" if language_code.startswith("en") else "Ventas"
    if rubro in WORK_LABEL_RUBROS:
        return "Work" if language_code.startswith("en") else "Trabajos"
    return "Documents" if language_code.startswith("en") else "Documentos"


def get_ui_labels(country_code=None, language_code=None):
    """
    Retorna el diccionario de labels según país e idioma.

    - country_code: código de país ISO2 en MAYÚSCULA (CL, US, MX, etc.)
    - language_code: 'es', 'en' o 'pt' (por ahora)

    Si no se encuentra una combinación, cae a Chile / español.
    """

    if not country_code:
        country_code = DEFAULT_COUNTRY_CODE

    country_code = str(country_code).strip().upper()
    language_code = (
        str(language_code or DEFAULT_LANGUAGE_CODE)
        .strip()
        .lower()
        .replace("_", "-")
    )

    # Brasil usa pt-br en configuración Django,
    # pero los labels internos usan pt.
    if country_code == "BR" and language_code == "pt-br":
        language_code = "pt"

    # Mapeo (país, idioma) -> diccionario
    mapping = {
        ("US", "en"): UI_LABELS_US_EN,
        ("CL", "es"): UI_LABELS_CL_ES,
        ("MX", "es"): UI_LABELS_MX_ES,
        ("PE", "es"): UI_LABELS_PE_ES,
        ("CO", "es"): UI_LABELS_CO_ES,
        ("AR", "es"): UI_LABELS_AR_ES,
        ("BR", "pt"): UI_LABELS_BR_PT,
        ("EC", "es"): UI_LABELS_EC_ES,
        ("VE", "es"): UI_LABELS_VE_ES,
        ("UY", "es"): UI_LABELS_UY_ES,
    }

    # Intentar combinación exacta
    labels = mapping.get((country_code, language_code))

    # Fallback: mismo país, idioma por defecto
    if labels is None:
        labels = mapping.get((country_code, DEFAULT_LANGUAGE_CODE))

    # Fallback final: Chile/español
    if labels is None:
        labels = UI_LABELS_CL_ES

    return labels
