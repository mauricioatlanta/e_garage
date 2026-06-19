"""
Vistas para Inspección de Ingreso de Vehículos.
Flujo: OT → detalle → "Registrar Inspección" → form → detalle inspección.
"""

import re
from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from taller.models.documento import Documento
from taller.models.inspeccion_ingreso import (
    DanoInspeccion,
    EvidenciaInspeccion,
    InspeccionIngreso,
    NIVEL_COMBUSTIBLE,
    ZONAS_VEHICULO,
    TIPOS_DANO,
    ESTADO_INSPECCION,
)
from taller.utils.email_helper import send_email_with_reply_to
from taller.templatetags.country_url import reverse_country_url

# Prefijos telefónicos por país (ISO 3166-1 alpha-2)
_DIAL_CODES = {
    "CL": "56",
    "US": "1",
    "MX": "52",
    "AR": "54",
    "UY": "598",
    "BR": "55",
    "PE": "51",
    "VE": "58",
}


def _telefono_para_wame(telefono: str, pais: str) -> str:
    """Devuelve el teléfono en formato E.164 sin '+' para usar en wa.me/<número>."""
    telefono = re.sub(r"[^\d+]", "", telefono or "")
    if not telefono:
        return ""
    if telefono.startswith("+"):
        return telefono[1:]
    dial = _DIAL_CODES.get(pais.upper(), "")
    if dial and not telefono.startswith(dial):
        # Quitar cero local inicial (ej. 0912... → 912...)
        telefono = dial + telefono.lstrip("0")
    return telefono


def _generar_texto_inspeccion(inspeccion, empresa_nombre: str) -> str:
    """Texto plano del reporte de inspección, reutilizable para WhatsApp y email."""
    vehiculo = str(inspeccion.vehiculo)
    fecha = inspeccion.fecha_hora.strftime("%d/%m/%Y %H:%M")
    km = (
        f"{inspeccion.kilometraje_ingreso:,} km"
        if inspeccion.kilometraje_ingreso
        else "No registrado"
    )
    combustible = inspeccion.get_nivel_combustible_display()

    danos = inspeccion.danos.all()
    if danos:
        lista_danos = "\n".join(
            "  • "
            + d.get_zona_display()
            + " → "
            + d.get_tipo_dano_display()
            + (f": {d.descripcion}" if d.descripcion else "")
            for d in danos
        )
    else:
        lista_danos = "  Sin daños registrados"

    obs = (
        f"\n\nObservaciones:\n{inspeccion.observaciones_generales}"
        if inspeccion.observaciones_generales
        else ""
    )

    return (
        f"*Inspección de Ingreso – {empresa_nombre}*\n"
        f"Vehículo: {vehiculo}\n"
        f"Fecha: {fecha}\n"
        f"Kilometraje: {km} | Combustible: {combustible}\n\n"
        f"Daños preexistentes:\n{lista_danos}"
        f"{obs}\n\n"
        "Este reporte fue generado al momento de la recepción del vehículo."
    )


@login_required
def crear_inspeccion_ingreso(request, documento_id):
    empresa = request.user.empresa
    documento = get_object_or_404(Documento, pk=documento_id, empresa=empresa)

    # Si ya existe, redirigir al detalle
    if hasattr(documento, "inspeccion_ingreso"):
        url = reverse_country_url(request, "documentos:ver_inspeccion_ingreso", documento.inspeccion_ingreso.pk)
        return redirect(url)

    if request.method == "POST":
        inspeccion = InspeccionIngreso(
            empresa=empresa,
            documento=documento,
            vehiculo=documento.vehiculo,
            realizada_por=request.user,
        )
        inspeccion.kilometraje_ingreso = request.POST.get("kilometraje_ingreso") or None
        inspeccion.nivel_combustible = request.POST.get("nivel_combustible", "medio")
        inspeccion.observaciones_generales = request.POST.get("observaciones_generales", "")
        inspeccion.firma_cliente = bool(request.POST.get("firma_cliente"))
        inspeccion.estado_inspeccion = "completada" if inspeccion.firma_cliente else "pendiente"
        inspeccion.save()

        # Daños (puede haber varios: zona_0, tipo_dano_0, descripcion_0, ...)
        i = 0
        while f"zona_{i}" in request.POST:
            zona = request.POST.get(f"zona_{i}", "").strip()
            tipo = request.POST.get(f"tipo_dano_{i}", "").strip()
            desc = request.POST.get(f"descripcion_{i}", "").strip()
            if zona and tipo:
                DanoInspeccion.objects.create(
                    inspeccion=inspeccion, zona=zona, tipo_dano=tipo, descripcion=desc
                )
            i += 1

        # Fotos (hasta 10 por inspección)
        for archivo in request.FILES.getlist("fotos"):
            ext = archivo.name.rsplit(".", 1)[-1].lower()
            tipo = "VIDEO" if ext in ("mp4", "mov", "avi", "webm") else "FOTO"
            desc = request.POST.get(
                f"desc_foto_{EvidenciaInspeccion.objects.filter(inspeccion=inspeccion).count()}", ""
            )
            EvidenciaInspeccion.objects.create(
                inspeccion=inspeccion,
                tipo=tipo,
                archivo=archivo,
                descripcion=desc,
            )

        messages.success(request, "Inspección de ingreso registrada.")
        url = reverse_country_url(request, "documentos:ver_inspeccion_ingreso", inspeccion.pk)
        return redirect(url)

    cliente = documento.cliente
    pais = getattr(empresa, "pais", "CL")
    empresa_nombre = empresa.nombre_taller

    # Pre-armar el link de WhatsApp aunque la inspección aún no exista,
    # para que el técnico pueda avisar al cliente que la está registrando.
    whatsapp_url_previo = None
    telefono_cliente = getattr(cliente, "telefono", None) if cliente else None
    if telefono_cliente:
        tel_wa = _telefono_para_wame(telefono_cliente, pais)
        if tel_wa:
            aviso = (
                f"Hola, estamos registrando la inspección de ingreso de su vehículo "
                f"({documento.vehiculo}) en {empresa_nombre}. "
                f"En breve le enviaremos el reporte completo."
            )
            whatsapp_url_previo = f"https://wa.me/{tel_wa}?text={quote(aviso)}"

    ctx = {
        "documento": documento,
        "nivel_combustible_choices": NIVEL_COMBUSTIBLE,
        "zonas_choices": ZONAS_VEHICULO,
        "tipos_dano_choices": TIPOS_DANO,
        "cliente": cliente,
        "cliente_email": getattr(cliente, "email", "") or "",
        "whatsapp_url_previo": whatsapp_url_previo,
    }
    return render(request, "taller/documentos/inspeccion_ingreso_form.html", ctx)


@login_required
def ver_inspeccion_ingreso(request, pk):
    empresa = request.user.empresa
    inspeccion = get_object_or_404(InspeccionIngreso, pk=pk, empresa=empresa)

    cliente = inspeccion.documento.cliente if inspeccion.documento_id else None
    empresa_nombre = empresa.nombre_taller
    pais = getattr(empresa, "pais", "CL")

    # URL de WhatsApp (wa.me) con mensaje pre-compuesto
    whatsapp_url = None
    telefono_cliente = getattr(cliente, "telefono", None) if cliente else None
    if telefono_cliente:
        tel_wa = _telefono_para_wame(telefono_cliente, pais)
        if tel_wa:
            mensaje_wa = _generar_texto_inspeccion(inspeccion, empresa_nombre)
            whatsapp_url = f"https://wa.me/{tel_wa}?text={quote(mensaje_wa)}"

    ctx = {
        "inspeccion": inspeccion,
        "danos": inspeccion.danos.all(),
        "evidencias": inspeccion.evidencias.all(),
        "cliente": cliente,
        "whatsapp_url": whatsapp_url,
        "cliente_email": getattr(cliente, "email", "") or "",
    }
    return render(request, "taller/documentos/inspeccion_ingreso_detalle.html", ctx)


@login_required
@require_POST
def marcar_firmada(request, pk):
    empresa = request.user.empresa
    inspeccion = get_object_or_404(InspeccionIngreso, pk=pk, empresa=empresa)
    inspeccion.firma_cliente = True
    inspeccion.estado_inspeccion = "firmada"
    inspeccion.save(update_fields=["firma_cliente", "estado_inspeccion"])
    messages.success(request, "Inspección marcada como firmada por el cliente.")
    url = reverse_country_url(request, "documentos:ver_inspeccion_ingreso", inspeccion.pk)
    return redirect(url)


@login_required
@require_POST
def enviar_inspeccion_email(request, pk):
    empresa = request.user.empresa
    inspeccion = get_object_or_404(InspeccionIngreso, pk=pk, empresa=empresa)

    email_destino = request.POST.get("email", "").strip()
    if not email_destino:
        messages.error(request, "Debe ingresar un correo electrónico de destino.")
        url = reverse_country_url(request, "documentos:ver_inspeccion_ingreso", pk)
        return redirect(url)

    empresa_nombre = empresa.nombre_taller
    texto = _generar_texto_inspeccion(inspeccion, empresa_nombre)
    # Quitar marcadores de negrita de WhatsApp (*) para el email
    texto_email = texto.replace("*", "")

    subject = f"Inspección de ingreso – {inspeccion.vehiculo}"

    try:
        send_email_with_reply_to(
            subject=subject,
            message=texto_email,
            recipient_list=[email_destino],
            fail_silently=False,
        )
        messages.success(request, f"Inspección enviada por correo a {email_destino}.")
    except Exception as exc:
        messages.error(request, f"Error al enviar el correo: {exc}")

    url = reverse_country_url(request, "documentos:ver_inspeccion_ingreso", pk)
    return redirect(url)
