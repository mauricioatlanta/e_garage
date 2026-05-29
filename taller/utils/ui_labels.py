"""
🌍 Diccionario Maestro de Términos por País - eGarage
=====================================================

Sistema centralizado de etiquetas UI por país.
Cada país usa su terminología real del rubro automotriz.

PRINCIPIOS:
- NO se cambia el backend (Documento)
- Solo se cambian etiquetas de interfaz
- Cada país usa su terminología real (como se habla en ese rubro)
- Donde existen diferencias locales (ej: folio, comprobante, OS), se respeta
"""

# 🇺🇸 USA - Inglés
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

# 🇨🇱 Chile - Español
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

# 🇲🇽 México - Español
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

# 🇵🇪 Perú - Español
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

# 🇨🇴 Colombia - Español
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

# 🇦🇷 Argentina - Español
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

# 🇧🇷 Brasil - Portugués
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

# 🇪🇨 Ecuador - Español
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

# 🇻🇪 Venezuela - Español
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

# 🇺🇾 Uruguay - Español
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

# Mapeo de país + idioma a diccionario de labels
COUNTRY_LABELS_MAP = {
    ("US", "en"): UI_LABELS_US_EN,
    ("CL", "es"): UI_LABELS_CL_ES,
    ("MX", "es"): UI_LABELS_MX_ES,
    ("PE", "es"): UI_LABELS_PE_ES,
    ("CO", "es"): UI_LABELS_CO_ES,
    ("AR", "es"): UI_LABELS_AR_ES,
    ("BR", "pt"): UI_LABELS_BR_PT,
    ("BR", "pt-br"): UI_LABELS_BR_PT,
    ("EC", "es"): UI_LABELS_EC_ES,
    ("VE", "es"): UI_LABELS_VE_ES,
    ("UY", "es"): UI_LABELS_UY_ES,
}

# Fallback por defecto (Chile)
DEFAULT_LABELS = UI_LABELS_CL_ES


def get_ui_labels(country_code, language_code=None):
    """
    Obtiene las etiquetas UI para un país e idioma específicos.

    Args:
        country_code: Código de país (ej: 'US', 'CL', 'MX', 'PE')
        language_code: Código de idioma (ej: 'en', 'es', 'pt'). Si es None,
                       se usa el idioma por defecto del país.

    Returns:
        dict: Diccionario con las etiquetas UI para el país/idioma

    Ejemplo:
        >>> labels = get_ui_labels('MX', 'es')
        >>> print(labels['documents_menu'])  # 'Documentos'
        >>> print(labels['document_number'])  # 'Folio'
    """
    if not country_code:
        return DEFAULT_LABELS

    country_code = str(country_code).strip().upper()

    # Si no se especifica idioma, intentar obtenerlo desde la configuración del país
    if not language_code:
        try:
            from taller.utils.country_config import get_country_config

            config = get_country_config(country_code)
            language_code = config.get("lang", "es")
        except Exception:
            language_code = "es"

    # Normalizar código de idioma
    language_code = str(language_code).strip().lower()

    # Buscar en el mapeo
    key = (country_code, language_code)
    if key in COUNTRY_LABELS_MAP:
        return COUNTRY_LABELS_MAP[key]

    # Si no hay match exacto, intentar solo con país (usar idioma por defecto)
    # Primero intentar con el idioma del país
    try:
        from taller.utils.country_config import get_country_config

        config = get_country_config(country_code)
        default_lang = config.get("lang", "es")
        key = (country_code, default_lang)
        if key in COUNTRY_LABELS_MAP:
            return COUNTRY_LABELS_MAP[key]
    except Exception:
        pass

    # Fallback: buscar cualquier idioma para ese país
    for (c, l), labels in COUNTRY_LABELS_MAP.items():
        if c == country_code:
            return labels

    # Último fallback: labels por defecto (Chile)
    return DEFAULT_LABELS


def get_label(country_code, language_code, label_key, default=None):
    """
    Obtiene una etiqueta específica para un país e idioma.

    Args:
        country_code: Código de país
        language_code: Código de idioma (opcional)
        label_key: Clave de la etiqueta (ej: 'documents_menu', 'document_number')
        default: Valor por defecto si no se encuentra la etiqueta

    Returns:
        str: Etiqueta traducida o valor por defecto

    Ejemplo:
        >>> label = get_label('MX', 'es', 'document_number')
        >>> print(label)  # 'Folio'
    """
    labels = get_ui_labels(country_code, language_code)
    return labels.get(label_key, default or label_key)


def get_all_available_labels():
    """
    Obtiene todos los diccionarios de labels disponibles.

    Returns:
        dict: Diccionario con todos los mapeos país+idioma -> labels
    """
    return COUNTRY_LABELS_MAP.copy()


def get_available_countries_for_labels():
    """
    Obtiene lista de países que tienen labels configurados.

    Returns:
        list: Lista de códigos de países
    """
    countries = set()
    for (country, _), _ in COUNTRY_LABELS_MAP.items():
        countries.add(country)
    return sorted(list(countries))
