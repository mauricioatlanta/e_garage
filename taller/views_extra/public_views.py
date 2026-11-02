"""
Vistas públicas para acceso de clientes a documentos sin autenticación.
Protegidas por UUID único en la URL.
"""

import logging

from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from taller.models.documento import Documento
from taller.models.company_settings import CompanySettings

log = logging.getLogger(__name__)


def _get_public_branding_context(documento, company_settings):
    empresa = documento.empresa
    logo_url = None
    if company_settings and getattr(company_settings, "logo", None):
        try:
            logo_url = company_settings.logo.url
        except Exception:
            logo_url = None
    elif getattr(empresa, "logo", None):
        try:
            logo_url = empresa.logo.url
        except Exception:
            logo_url = None

    return {
        "LOGO_PERSONALIZADO": logo_url,
        "COLOR_PRIMARIO": (
            getattr(company_settings, "primary_color", None)
            or getattr(documento.empresa, "color", None)
            or "#0d6efd"
        ),
        "COLOR_SECUNDARIO": getattr(company_settings, "secondary_color", None) or "#6c757d",
        "NOMBRE_EMPRESA_PERSONALIZADO": (
            getattr(company_settings, "company_name", None) or documento.empresa.nombre_taller
        ),
        "COMPANY_TERMS": getattr(company_settings, "terms_and_conditions", "") or "",
        "COMPANY_BANK": getattr(company_settings, "bank_details", "") or "",
    }


def detalle_presupuesto_publico(request, uuid):
    """
    Vista pública para que el cliente vea su presupuesto sin login.
    Protegida por UUID único en la URL.

    El context processor 'logo_empresa' automáticamente cargará:
    - LOGO_PERSONALIZADO
    - COLOR_PRIMARIO
    - COLOR_SECUNDARIO
    - NOMBRE_EMPRESA_PERSONALIZADO
    - COMPANY_TERMS
    - COMPANY_BANK
    """
    documento = get_object_or_404(
        Documento.objects.select_related("empresa", "cliente", "vehiculo").prefetch_related(
            "lineas_repuesto__repuesto", "lineas_servicio", "lineas_otro_servicio"
        ),
        uuid=uuid,
        tipo="PRES",
    )

    # Verificar que el documento no esté anulado
    if documento.estado == "ANULADO":
        return render(
            request,
            "taller/publico/documento_anulado.html",
            {"documento": documento},
            status=404,
        )

    if documento.estado != "EMITIDO":
        raise Http404("Documento no disponible")

    # Obtener configuración de la empresa para branding
    try:
        company_settings = CompanySettings.objects.filter(user=documento.empresa.user).first()
    except Exception:
        company_settings = None

    # Verificar si ya fue aprobado
    ya_aprobado = documento.approved_at is not None

    # Generar link de WhatsApp para enviar comprobante de pago
    whatsapp_pago_url = None
    if documento.cliente.telefono and (
        documento.estado_pago == "NO_PAGADO" or documento.estado_pago == "PARCIAL"
    ):
        try:
            from taller.reportes.services.document_output_service import DocumentOutputService

            whatsapp_pago_url = DocumentOutputService.generate_whatsapp_link_comprobante(
                documento, request
            )
        except Exception as e:
            log.debug(f"Error generando link WhatsApp para comprobante: {e}")

    context = {
        "documento": documento,
        "company_settings": company_settings,
        "ya_aprobado": ya_aprobado,
        "cliente": documento.cliente,
        "vehiculo": documento.vehiculo,
        "whatsapp_pago_url": whatsapp_pago_url,
    }
    context.update(_get_public_branding_context(documento, company_settings))

    return render(
        request,
        "taller/publico/presupuesto_cliente.html",
        context,
    )


@require_POST
def aprobar_presupuesto(request, uuid):
    """
    Vista para que el cliente apruebe el presupuesto.
    Guarda la fecha de aprobación y notifica al taller.
    """
    documento = get_object_or_404(
        Documento.objects.select_related("empresa", "cliente"),
        uuid=uuid,
        tipo="PRES",
    )

    if documento.estado != "EMITIDO":
        messages.error(request, "Este presupuesto ya no esta disponible para aprobacion.")
        return redirect("publico:ver_presupuesto", uuid=uuid)

    # Verificar que no esté ya aprobado
    if documento.approved_at:
        messages.info(
            request,
            "Este presupuesto ya fue aprobado anteriormente.",
        )
        return redirect("publico:ver_presupuesto", uuid=uuid)

    # Guardar aprobación
    documento.approved_at = timezone.now()
    documento.approved_by = f"{documento.cliente.nombre} {documento.cliente.apellido or ''}".strip()
    documento.approved_ip = get_client_ip(request)
    documento.save(update_fields=["approved_at", "approved_by", "approved_ip"])

    # Notificar al taller
    try:
        notificar_aprobacion_taller(documento)
    except Exception as e:
        log.error(f"Error notificando aprobación al taller: {e}", exc_info=True)
        # No fallar la aprobación si la notificación falla

    messages.success(
        request,
        f"¡Presupuesto aprobado exitosamente! {documento.empresa.nombre_taller} ha sido notificado y comenzará el trabajo.",
    )

    return redirect("publico:ver_presupuesto", uuid=uuid)


def get_client_ip(request):
    """Obtiene la IP real del cliente"""
    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def notificar_aprobacion_taller(documento):
    """
    Notifica al taller que el cliente aprobó el presupuesto.
    Puede enviar email, WhatsApp, o crear una notificación en el sistema.
    """
    empresa = documento.empresa
    cliente = documento.cliente

    # Obtener configuración de notificaciones
    try:
        from taller.models.configuracion_notificacion import ConfiguracionNotificacion

        config_notif = ConfiguracionNotificacion.objects.filter(empresa=empresa).first()
    except Exception:
        config_notif = None

    # Mensaje de notificación
    mensaje = (
        f"🎉 ¡Presupuesto Aprobado!\n\n"
        f"Cliente: {cliente.nombre} {cliente.apellido or ''}\n"
        f"Documento: {documento.get_tipo_display()} {documento.numero_documento or documento.numero}\n"
        f"Total: ${documento.total:,.0f}\n"
        f"Fecha de aprobación: {documento.approved_at.strftime('%d/%m/%Y %H:%M')}\n"
        f"\n¡Es hora de comenzar el trabajo! 🚗✨"
    )

    # Enviar email si está configurado
    email_enabled = config_notif.email_activo if config_notif else True
    if email_enabled and empresa.user.email:
        try:
            from django.conf import settings
            from taller.utils.email_helper import get_branded_from_email, send_email_with_reply_to

            send_email_with_reply_to(
                subject=f"✅ Presupuesto Aprobado - {documento.numero_documento or documento.numero}",
                message=mensaje,
                from_email=get_branded_from_email(
                    getattr(settings, "DEFAULT_FROM_EMAIL", "support@egarage.cl")
                ),
                recipient_list=[empresa.user.email],
                fail_silently=True,
            )
            log.info(f"Email de aprobación enviado a {empresa.user.email}")
        except Exception as e:
            log.error(f"Error enviando email de aprobación: {e}")

    # Enviar WhatsApp si está configurado
    if config_notif and config_notif.whatsapp_activo:
        try:
            from taller.utils.notificaciones_suscripcion import enviar_whatsapp_a_numero

            telefono_taller = getattr(empresa, "telefono", None) or getattr(
                config_notif, "whatsapp_numero_business", None
            )

            if telefono_taller:
                enviar_whatsapp_a_numero(
                    telefono=telefono_taller,
                    mensaje=mensaje,
                    config_notif=config_notif,
                )
                log.info(f"WhatsApp de aprobación enviado a {telefono_taller}")
        except Exception as e:
            log.error(f"Error enviando WhatsApp de aprobación: {e}")

    # Crear notificación en el sistema (si tienes un modelo de notificaciones)
    try:
        from taller.models.notificacion import Notificacion

        Notificacion.objects.create(
            usuario=empresa.user,
            titulo="Presupuesto Aprobado",
            mensaje=mensaje,
            tipo="APROBACION",
            url=f"/documentos/ver/{documento.id}/",
        )
    except Exception:
        # Si no existe el modelo de notificaciones, simplemente ignorar
        pass
