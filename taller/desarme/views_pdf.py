# PDF Recibo/Invoice, panel impresión, enlace público, WhatsApp y email.

import base64
from io import BytesIO
from pathlib import Path
from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from weasyprint import CSS, HTML

from taller.models.documento import Documento
from taller.utils.email_helper import get_branded_from_email, get_support_reply_to

from .views import _empresa_or_redirect


def _document_label(documento):
    tipo = (getattr(documento, "tipo", "") or "").lower()
    if tipo == "invoice":
        return "Invoice"
    numero = (getattr(documento, "numero", "") or "").strip().upper()
    if numero.startswith("INV-"):
        return "Invoice"
    return "Recibo"


def _document_filename(documento):
    base = (
        getattr(documento, "numero_documento", None)
        or getattr(documento, "numero", None)
        or f"DOC-{documento.id}"
    )
    if hasattr(base, "strip"):
        base = base.strip()
    if not base:
        base = f"DOC-{documento.id}"
    safe = "".join(c for c in str(base) if c.isalnum() or c in "-_")
    return f"{safe or documento.id}.pdf"


def _get_logo_url(request, empresa):
    if not empresa:
        return None
    try:
        cs = getattr(getattr(empresa, "user", None), "company_settings", None)
        if cs and getattr(cs, "logo", None):
            try:
                return request.build_absolute_uri(cs.logo.url)
            except Exception:
                pass
    except Exception:
        pass
    if hasattr(empresa, "configuracion"):
        config = getattr(empresa, "configuracion", None)
        if config and getattr(config, "logo", None):
            try:
                return request.build_absolute_uri(config.logo.url)
            except Exception:
                pass
    if getattr(empresa, "logo", None):
        try:
            return request.build_absolute_uri(empresa.logo.url)
        except Exception:
            pass
    return None


def _generated_at():
    now = timezone.now()
    return timezone.localtime(now) if timezone.is_aware(now) else now


def _line_subtotal(linea):
    try:
        if isinstance(linea, dict):
            return linea.get("subtotal", 0) or 0
        return getattr(linea, "subtotal", 0) or 0
    except Exception:
        return 0


def _build_pdf_line_items(documento):
    items = []

    try:
        lineas_repuesto = list(documento.lineas_repuesto.all().order_by("id"))
    except Exception:
        lineas_repuesto = []
    try:
        lineas_servicio = list(documento.lineas_servicio.all().order_by("id"))
    except Exception:
        lineas_servicio = []
    try:
        lineas_otro_servicio = list(documento.lineas_otro_servicio.all().order_by("id"))
    except Exception:
        lineas_otro_servicio = []

    for linea in lineas_repuesto:
        code = getattr(linea, "codigo", "") or getattr(getattr(linea, "repuesto", None), "codigo", "")
        items.append(
            {
                "tipo": "Repuesto",
                "nombre": getattr(linea, "nombre", "") or str(getattr(linea, "repuesto", "")),
                "codigo": code,
                "cantidad": getattr(linea, "cantidad", 1) or 1,
                "precio_unitario": getattr(linea, "precio_unitario", 0) or 0,
                "subtotal": _line_subtotal(linea),
            }
        )

    for linea in lineas_servicio:
        items.append(
            {
                "tipo": "Servicio",
                "nombre": getattr(linea, "nombre", "") or str(getattr(linea, "servicio", "")),
                "codigo": "",
                "cantidad": getattr(linea, "cantidad", 1) or 1,
                "precio_unitario": getattr(linea, "precio_unitario", 0) or 0,
                "subtotal": _line_subtotal(linea),
            }
        )

    for linea in lineas_otro_servicio:
        empresa_externa = getattr(linea, "empresa_externa", "") or ""
        items.append(
            {
                "tipo": "Servicio externo",
                "nombre": getattr(linea, "nombre", "") or str(getattr(linea, "servicio", "")),
                "codigo": empresa_externa,
                "cantidad": getattr(linea, "cantidad", 1) or 1,
                "precio_unitario": getattr(linea, "precio_cliente", 0) or 0,
                "subtotal": _line_subtotal(linea),
            }
        )

    return items, lineas_repuesto, lineas_servicio, lineas_otro_servicio


def _build_pdf_context(request, documento):
    empresa = getattr(documento, "empresa", None)
    cliente = getattr(documento, "cliente", None)
    vehiculo = getattr(documento, "vehiculo", None)

    cs = None
    try:
        cs = getattr(getattr(empresa, "user", None), "company_settings", None)
    except Exception:
        cs = None

    line_items, lineas_repuesto, lineas_servicio, lineas_otro_servicio = _build_pdf_line_items(
        documento
    )

    line_subtotal = sum(_line_subtotal(item) for item in line_items)
    subtotal = line_subtotal or (
        (getattr(documento, "neto_repuestos", 0) or 0)
        + (getattr(documento, "neto_servicios", 0) or 0)
        + (getattr(documento, "neto_otros_servicios", 0) or 0)
    )
    total = getattr(documento, "total", None)
    if not total:
        total = subtotal + (getattr(documento, "tax_amount", 0) or 0) - (
            getattr(documento, "descuento", 0) or 0
        )

    public_url = _public_document_url(request, documento)
    qr_data_uri = None
    try:
        import qrcode

        qr_data_uri = _build_qr_data_uri(public_url)
    except ImportError:
        pass

    return {
        "documento": documento,
        "empresa": empresa,
        "company_settings": cs,
        "company_name": (getattr(cs, "company_name", "") or "").strip()
        or (getattr(empresa, "empresa", "") or "").strip()
        or (getattr(empresa, "nombre_taller", "") or "").strip(),
        "company_tagline": (getattr(cs, "tagline", "") or "").strip(),
        "company_address": (getattr(cs, "address", "") or "").strip()
        or (getattr(empresa, "direccion", "") or "").strip(),
        "company_phone": (getattr(cs, "phone", "") or "").strip()
        or (getattr(empresa, "telefono", "") or "").strip(),
        "company_email": (getattr(cs, "email", "") or "").strip()
        or (getattr(empresa, "email", "") or "").strip(),
        "company_website": (getattr(cs, "website", "") or "").strip(),
        "cliente": cliente,
        "vehiculo": vehiculo,
        "line_items": line_items,
        "lineas_repuesto": lineas_repuesto,
        "lineas_servicio": lineas_servicio,
        "lineas_otro_servicio": lineas_otro_servicio,
        "subtotal": subtotal,
        "tax_amount": getattr(documento, "tax_amount", 0) or 0,
        "descuento": getattr(documento, "descuento", 0) or 0,
        "total": total,
        "total_sin_tax": total - (getattr(documento, "tax_amount", 0) or 0),
        "document_label": _document_label(documento),
        "logo_url": _get_logo_url(request, empresa),
        "generated_at": _generated_at(),
        "pdf_mode": True,
        "public_url": public_url,
        "qr_data_uri": qr_data_uri,
    }


def _build_qr_data_uri(value):
    import qrcode

    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(value)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _pdf_stylesheets():
    base_dir = getattr(settings, "BASE_DIR", Path(__file__).resolve().parent.parent.parent)
    css_path = Path(base_dir) / "static" / "css" / "documentos" / "pdf_documento_profesional.css"
    return [CSS(filename=str(css_path))] if css_path.exists() else []


def _render_documento_pdf_bytes(request, documento):
    html_string = render_to_string(
        "taller/documentos/pdf/documento_profesional.html",
        context=_build_pdf_context(request, documento),
        request=request,
    )
    return HTML(
        string=html_string,
        base_url=request.build_absolute_uri("/"),
    ).write_pdf(stylesheets=_pdf_stylesheets())


def _build_public_token(documento):
    signer = TimestampSigner(salt="documento-publico")
    return signer.sign(str(documento.id))


def _unsign_public_token(token, max_age=60 * 60 * 24 * 30):
    signer = TimestampSigner(salt="documento-publico")
    try:
        raw = signer.unsign(token, max_age=max_age)
        return int(raw)
    except (BadSignature, SignatureExpired, ValueError):
        return None


def _public_document_url(request, documento):
    token = _build_public_token(documento)
    # País del enlace público según la empresa del documento, no según la ruta por la que entró el usuario.
    # Así empresa US → siempre /us/... o /us/en/..., empresa CL → /cl/..., empresa UY → /uy/...
    from taller.templatetags.country_url import _country_ns_from_empresa

    empresa = getattr(documento, "empresa", None)
    country_ns = _country_ns_from_empresa(empresa)
    viewname = f"{country_ns}:documentos:ver_documento_publico"
    return request.build_absolute_uri(reverse(viewname, args=[token]))


def _get_documento_queryset():
    return Documento.objects.select_related("empresa", "cliente", "vehiculo").prefetch_related(
        "lineas_repuesto"
    )


def _get_documento_for_request(request, documento_id):
    queryset = _get_documento_queryset()
    if getattr(request.user, "is_staff", False) or getattr(request.user, "is_superuser", False):
        return get_object_or_404(queryset, pk=documento_id)

    empresa = _empresa_or_redirect(request)
    if not empresa:
        raise Http404("Sin empresa.")
    return get_object_or_404(queryset, pk=documento_id, empresa=empresa)


@login_required
def descargar_documento_pdf(request, documento_id):
    documento = _get_documento_for_request(request, documento_id)
    pdf_bytes = _render_documento_pdf_bytes(request, documento)
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{_document_filename(documento)}"'
    return response


@login_required
def imprimir_documento(request, documento_id):
    documento = _get_documento_for_request(request, documento_id)
    context = _build_pdf_context(request, documento)
    context["public_url"] = _public_document_url(request, documento)
    context["print_mode"] = True
    return render(request, "taller/documentos/imprimir_documento.html", context)


def ver_documento_publico(request, token):
    documento_id = _unsign_public_token(token)
    if not documento_id:
        raise Http404("Enlace inválido o expirado.")
    documento = get_object_or_404(_get_documento_queryset(), pk=documento_id)
    context = _build_pdf_context(request, documento)
    context["public_url"] = _public_document_url(request, documento)
    context["public_mode"] = True
    return render(request, "taller/documentos/publico/documento_publico.html", context)


@login_required
def compartir_documento_whatsapp(request, documento_id):
    documento = _get_documento_for_request(request, documento_id)
    cliente = getattr(documento, "cliente", None)
    public_url = _public_document_url(request, documento)
    label = _document_label(documento)
    numero = (
        getattr(documento, "numero_documento", None)
        or getattr(documento, "numero", None)
        or f"#{documento.id}"
    )
    mensaje = (
        f"Hola {getattr(cliente, 'nombre', '')}, "
        f"te compartimos tu {label} {numero}. "
        f"Puedes verlo aquí: {public_url}"
    )
    wa_url = f"https://wa.me/?text={quote(mensaje)}"
    return redirect(wa_url)


@login_required
def enviar_documento_email(request, documento_id):
    documento = _get_documento_for_request(request, documento_id)
    cliente = getattr(documento, "cliente", None)
    destino = getattr(cliente, "email", None)

    if not destino:
        messages.error(request, "El cliente no tiene email configurado.")
        return redirect("documentos:imprimir_documento", documento_id=documento.id)

    label = _document_label(documento)
    numero = (
        getattr(documento, "numero_documento", None)
        or getattr(documento, "numero", None)
        or f"#{documento.id}"
    )
    empresa_obj = getattr(documento, "empresa", None)
    public_url = _public_document_url(request, documento)

    body = render_to_string(
        "taller/documentos/email/documento_email.txt",
        {
            "cliente": cliente,
            "documento": documento,
            "document_label": label,
            "public_url": public_url,
            "empresa": empresa_obj,
        },
    )

    email = EmailMessage(
        subject=f"{label} {numero}",
        body=body,
        from_email=get_branded_from_email(),
        to=[destino],
        reply_to=[get_support_reply_to()],
    )
    email.attach(
        _document_filename(documento),
        _render_documento_pdf_bytes(request, documento),
        "application/pdf",
    )
    email.send(fail_silently=False)

    messages.success(request, f"{label} enviado por email a {destino}.")
    return redirect("documentos:imprimir_documento", documento_id=documento.id)
