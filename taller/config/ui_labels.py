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
    "documents_menu": "INVOICED",
    "new_document": "New Invoice",
    "document_center": "Invoices",
    "document_type_invoice": "Invoice",
    "document_type_estimate": "Estimate",
    "document_type_work_order": "Work Order",
    "document_number": "Invoice Number",
    "create_button": "Create Invoice",
    "edit_button": "Edit Invoice",
}


# ---------------------------
# Chile - Español
# ---------------------------
UI_LABELS_CL_ES = {
    "documents_menu": "Documentos",
    "new_document": "Nuevo Documento",
    "document_center": "Documentos",
    "document_type_invoice": "Factura",
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
    "document_type_invoice": "Factura",
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
    "document_type_invoice": "Factura",
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
    "document_type_invoice": "Factura",
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
    "document_type_invoice": "Factura",
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
    "document_type_invoice": "Factura",
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
    "document_type_invoice": "Factura",
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
    "document_type_invoice": "Factura",
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


def get_ui_labels(country_code=None, language_code=None):
    """
    Retorna el diccionario de labels según país e idioma.

    - country_code: código de país ISO2 en MAYÚSCULA (CL, US, MX, etc.)
    - language_code: 'es', 'en' o 'pt' (por ahora)

    Si no se encuentra una combinación, cae a Chile / español.
    """

    if not country_code:
        country_code = DEFAULT_COUNTRY_CODE

    country_code = country_code.upper()
    language_code = (language_code or DEFAULT_LANGUAGE_CODE).lower()

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
