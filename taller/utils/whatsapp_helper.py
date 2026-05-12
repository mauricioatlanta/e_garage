from django.conf import settings

from taller.whatsapp.helpers import build_document_wa_message, build_wa_link, normalize_phone


COUNTRY_DIAL_CODES = {
    "AR": "54",
    "BR": "55",
    "CL": "56",
    "CO": "57",
    "EC": "593",
    "MX": "52",
    "PE": "51",
    "US": "1",
    "UY": "598",
    "VE": "58",
}


def get_country_dial_code(country_code="CL"):
    return COUNTRY_DIAL_CODES.get((country_code or "CL").upper(), "56")


def clean_phone_number(phone, country_code="56"):
    """
    Limpia el telefono a formato E.164 sin signo +, listo para wa.me.
    """
    return normalize_phone(phone, country_code)


def _build_absolute_url(path, request=None):
    if request is not None:
        return request.build_absolute_uri(path)

    base_url = (
        getattr(settings, "SITE_URL", None)
        or getattr(settings, "BASE_URL", None)
        or "https://egarage.cl"
    ).rstrip("/")
    return f"{base_url}{path}"


def _get_vehicle_display(documento):
    vehiculo = getattr(documento, "vehiculo", None)
    if not vehiculo:
        return ""

    patente = getattr(vehiculo, "patente", "") or ""
    marca = (
        getattr(vehiculo, "marca_texto", None)
        or getattr(getattr(vehiculo, "marca", None), "nombre", None)
        or ""
    )
    modelo = (
        getattr(vehiculo, "modelo_texto", None)
        or getattr(getattr(vehiculo, "modelo", None), "nombre", None)
        or ""
    )

    if marca and modelo and patente:
        return f"{marca} {modelo} ({patente})"
    if marca and modelo:
        return f"{marca} {modelo}"
    if patente:
        return patente
    return "vehiculo"


def get_document_public_url(documento, request=None):
    """
    Retorna la mejor URL publica disponible para el documento.
    """
    if documento is None:
        return None

    if getattr(documento, "tipo", None) == "PRES" and getattr(documento, "uuid", None):
        try:
            return documento.get_public_url(request=request)
        except Exception:
            pass

    seguimiento_publico = getattr(documento, "seguimiento_publico", None)
    token = getattr(seguimiento_publico, "token", None)
    if token:
        from django.urls import reverse

        path = reverse("documentos:seguimiento_publico", kwargs={"token": token})
        return _build_absolute_url(path, request=request)

    return None


def build_budget_whatsapp_message(documento, public_url):
    cliente = getattr(documento, "cliente", None)
    empresa = getattr(documento, "empresa", None)
    cliente_nombre = getattr(cliente, "nombre", None) or "Cliente"
    empresa_nombre = getattr(empresa, "nombre_taller", None) or "eGarage"
    vehiculo_display = _get_vehicle_display(documento)
    language = "en" if getattr(empresa, "pais", "").upper() == "US" else "es"

    if language == "en":
        greeting = f"Hello *{cliente_nombre}*"
        detail = (
            f"We are sending you your estimate from *{empresa_nombre}*"
            if not vehiculo_display
            else f"We are sending you the estimate for your vehicle *{vehiculo_display}*"
        )
        call_to_action = "You can review it, download the PDF, and *approve it online* here:"
    else:
        greeting = f"Hola *{cliente_nombre}*"
        detail = (
            f"Te envio tu presupuesto de *{empresa_nombre}*"
            if not vehiculo_display
            else f"Te envio el presupuesto de tu vehiculo *{vehiculo_display}*"
        )
        call_to_action = "Puedes revisarlo, descargar el PDF y *aprobarlo online* aqui:"

    return "\n\n".join([greeting, detail, call_to_action, public_url])


def get_document_whatsapp_url(documento, request=None, pdf_url=None, message_override=None):
    """
    Genera el link wa.me mas conveniente para el documento.
    """
    if documento is None:
        return None

    cliente = getattr(documento, "cliente", None)
    if cliente is None:
        return None

    telefono = getattr(cliente, "telefono", None) or getattr(cliente, "phone", None)
    empresa = getattr(documento, "empresa", None)
    dial_code = get_country_dial_code(getattr(empresa, "pais", "CL"))

    if not clean_phone_number(telefono, dial_code):
        return None

    if message_override:
        message = str(message_override)
    else:
        public_url = get_document_public_url(documento, request=request)

        if getattr(documento, "tipo", None) == "PRES" and public_url:
            message = build_budget_whatsapp_message(documento, public_url)
        else:
            url_documento = public_url or pdf_url
            if not url_documento and request is not None:
                from django.urls import reverse

                try:
                    path = reverse("documentos:descargar_pdf", kwargs={"pk": documento.id})
                    url_documento = request.build_absolute_uri(path)
                except Exception:
                    url_documento = None

            tipo_doc = (
                (documento.get_tipo_display() if hasattr(documento, "get_tipo_display") else None)
                or getattr(documento, "tipo_documento", None)
                or "Documento"
            )
            numero_doc = (
                getattr(documento, "numero_documento", None)
                or getattr(documento, "numero", None)
                or str(getattr(documento, "id", ""))
            )
            total = float(getattr(documento, "total", 0) or 0)
            empresa_nombre = getattr(empresa, "nombre_taller", None) or "eGarage"
            cliente_nombre = getattr(cliente, "nombre", None) or "Cliente"
            language = "en" if getattr(empresa, "pais", "").upper() == "US" else "es"

            message = build_document_wa_message(
                documento=documento,
                cliente_nombre=cliente_nombre,
                tipo_doc=tipo_doc,
                numero_doc=numero_doc,
                total=total,
                empresa_nombre=empresa_nombre,
                url_documento=url_documento,
                vehiculo_info=_get_vehicle_display(documento) or None,
                language=language,
            )

    return build_wa_link(telefono, message, dial_code)
