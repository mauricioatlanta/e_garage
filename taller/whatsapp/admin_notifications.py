"""
Notificaciones WhatsApp para admin de eGarage
Se disparan cuando hay nueva suscripción o renovación
"""

import logging
import uuid
from typing import Optional
from django.conf import settings
from django.db import transaction

from .providers import get_whatsapp_provider

logger = logging.getLogger(__name__)


def notify_admin_new_subscription(
    empresa,
    plan: str,
    monto: float,
    es_nueva_suscripcion: bool = True,
    dias_renovados: Optional[int] = None,
    comprobante_pago_id: Optional[int] = None,
    pago_pendiente_id: Optional[int] = None,
    operation_uuid: Optional[str] = None,
) -> bool:
    """
    Notificar al admin de eGarage sobre nueva suscripción o renovación

    🔒 IDEMPOTENCIA REAL: Basada en idempotency_key único (empresa_id + event_type + ref_id)
    No envía dos veces la misma notificación para el mismo evento.

    Args:
        empresa: Instancia de Empresa
        plan: Plan de suscripción (ej: "basico", "premium")
        monto: Monto de la suscripción/renovación
        es_nueva_suscripcion: True si es nueva suscripción, False si es renovación
        dias_renovados: Días renovados (solo para renovaciones)
        comprobante_pago_id: ID del ComprobantePago (para idempotencia)
        pago_pendiente_id: ID del PagoPendiente (para idempotencia)
        operation_uuid: UUID de operación (si no hay comprobante/pago)

    Returns:
        True si se envió correctamente, False en caso contrario
    """
    try:
        # 🔒 IDEMPOTENCIA REAL: Generar clave única y verificar en DB
        event_type = "nueva_suscripcion" if es_nueva_suscripcion else "renovacion"

        try:
            from .models import WhatsAppAdminNotificationLog

            # Generar idempotency_key
            idempotency_key = WhatsAppAdminNotificationLog.generate_idempotency_key(
                empresa_id=empresa.id,
                event_type=event_type,
                comprobante_pago_id=comprobante_pago_id,
                pago_pendiente_id=pago_pendiente_id,
                operation_uuid=operation_uuid,
            )

            # Verificar si ya existe notificación con esta clave
            existing = WhatsAppAdminNotificationLog.objects.filter(
                idempotency_key=idempotency_key
            ).first()

            if existing:
                logger.info(
                    f"⚠️ Notificación WhatsApp admin ya enviada (idempotency_key={idempotency_key}) - "
                    f"Saltando (idempotencia real)"
                )
                return True  # Ya se notificó, considerar éxito
        except Exception as e:
            # Si falla la verificación de idempotencia, continuar (no romper flujo)
            logger.warning(f"Error verificando idempotencia (continuando): {e}")

        # Verificar si las notificaciones están habilitadas
        enabled = getattr(settings, "WHATSAPP_ADMIN_NOTIFICATIONS_ENABLED", False)
        if not enabled:
            logger.debug("WhatsApp admin notifications disabled, skipping")
            return False

        # Obtener número de admin desde settings
        admin_number = getattr(settings, "WHATSAPP_ADMIN_NUMBER", None)
        if not admin_number:
            logger.warning("WHATSAPP_ADMIN_NUMBER no configurado, no se puede enviar notificación")
            return False

        # Obtener email de soporte para el mensaje
        support_email = getattr(settings, "SUPPORT_EMAIL", "support@egarage.cl")

        # Determinar idioma según país
        country = getattr(empresa, "pais", "CL").upper()
        language = "en" if country == "US" else "es"

        # Obtener nombre del plan
        plan_display = (
            dict(empresa.PLAN_CHOICES).get(plan, plan) if hasattr(empresa, "PLAN_CHOICES") else plan
        )

        # Construir mensaje según tipo de evento
        if es_nueva_suscripcion:
            if language == "en":
                message = f"""🚗 *New Subscription - eGarage*

*Company:*
🏢 {empresa.nombre_taller}
🌍 Country: {country}
📧 Email: {getattr(empresa.user, 'email', 'N/A') if hasattr(empresa, 'user') else 'N/A'}

*Subscription:*
📦 Plan: {plan_display}
💰 Amount: ${monto:,.2f}
📅 Start: {empresa.fecha_inicio.strftime('%Y-%m-%d') if hasattr(empresa, 'fecha_inicio') and empresa.fecha_inicio else 'N/A'}
📅 Expires: {empresa.fecha_fin.strftime('%Y-%m-%d') if hasattr(empresa, 'fecha_fin') and empresa.fecha_fin else 'N/A'}

📧 Support: {support_email}"""
            else:
                message = f"""🚗 *Nueva Suscripción - eGarage*

*Empresa:*
🏢 {empresa.nombre_taller}
🌍 País: {country}
📧 Email: {getattr(empresa.user, 'email', 'N/A') if hasattr(empresa, 'user') else 'N/A'}

*Suscripción:*
📦 Plan: {plan_display}
💰 Monto: ${monto:,.2f}
📅 Inicio: {empresa.fecha_inicio.strftime('%d/%m/%Y') if hasattr(empresa, 'fecha_inicio') and empresa.fecha_inicio else 'N/A'}
📅 Expira: {empresa.fecha_fin.strftime('%d/%m/%Y') if hasattr(empresa, 'fecha_fin') and empresa.fecha_fin else 'N/A'}

📧 Soporte: {support_email}"""
        else:
            # Renovación
            if language == "en":
                message = f"""✅ *Subscription Renewed - eGarage*

*Company:*
🏢 {empresa.nombre_taller}
🌍 Country: {country}
📧 Email: {getattr(empresa.user, 'email', 'N/A') if hasattr(empresa, 'user') else 'N/A'}

*Renewal:*
📦 Plan: {plan_display}
💰 Amount: ${monto:,.2f}
📅 Period: {dias_renovados or 30} days
📅 Expires: {empresa.fecha_fin.strftime('%Y-%m-%d') if hasattr(empresa, 'fecha_fin') and empresa.fecha_fin else 'N/A'}

📧 Support: {support_email}"""
            else:
                message = f"""✅ *Suscripción Renovada - eGarage*

*Empresa:*
🏢 {empresa.nombre_taller}
🌍 País: {country}
📧 Email: {getattr(empresa.user, 'email', 'N/A') if hasattr(empresa, 'user') else 'N/A'}

*Renovación:*
📦 Plan: {plan_display}
💰 Monto: ${monto:,.2f}
📅 Período: {dias_renovados or 30} días
📅 Expira: {empresa.fecha_fin.strftime('%d/%m/%Y') if hasattr(empresa, 'fecha_fin') and empresa.fecha_fin else 'N/A'}

📧 Soporte: {support_email}"""

        # Obtener provider y enviar
        # 🔒 FAIL-SAFE: Nunca debe romper el flujo principal
        provider_name = "unknown"
        try:
            provider = get_whatsapp_provider()
            provider_name = getattr(settings, "WHATSAPP_ADMIN_PROVIDER", "dummy")
            result = provider.send(admin_number, message)

            # Registrar en auditoría
            from .audit_log import log_whatsapp_admin_attempt

            log_whatsapp_admin_attempt(
                empresa_id=empresa.id,
                empresa_nombre=empresa.nombre_taller,
                event_type="nueva_suscripcion" if es_nueva_suscripcion else "renovacion",
                provider=provider_name,
                success=result.get("success", False),
                error=result.get("error"),
                message_id=result.get("message_id"),
            )

            if result.get("success"):
                logger.info(
                    f"✅ Notificación WhatsApp admin enviada: {'Nueva suscripción' if es_nueva_suscripcion else 'Renovación'}"
                )

                # Guardar registro en DB (idempotencia real)
                _save_notification_record(
                    empresa=empresa,
                    event_type=event_type,
                    plan=plan,
                    monto=monto,
                    provider=provider_name,
                    success=True,
                    message_id=result.get("message_id"),
                    idempotency_key=idempotency_key,
                    comprobante_pago_id=comprobante_pago_id,
                    pago_pendiente_id=pago_pendiente_id,
                )

                return True
            else:
                # Log error pero NO lanzar excepción
                error_msg = result.get("error", "Unknown error")
                logger.warning(
                    f"⚠️ Error enviando notificación WhatsApp admin (no crítico): {error_msg}"
                )

                # Guardar registro en DB (idempotencia real)
                _save_notification_record(
                    empresa=empresa,
                    event_type=event_type,
                    plan=plan,
                    monto=monto,
                    provider=provider_name,
                    success=False,
                    error=error_msg,
                    idempotency_key=idempotency_key,
                    comprobante_pago_id=comprobante_pago_id,
                    pago_pendiente_id=pago_pendiente_id,
                )

                return False
        except Exception as e:
            # 🔒 CRÍTICO: Capturar cualquier excepción y no propagarla
            # El proceso de suscripción/pago NO debe fallar por WhatsApp
            logger.error(
                f"❌ Excepción en notify_admin_new_subscription (ignorada para no romper flujo): {e}",
                exc_info=True,
            )

            # Registrar en auditoría incluso si hay excepción
            try:
                from .audit_log import log_whatsapp_admin_attempt

                log_whatsapp_admin_attempt(
                    empresa_id=empresa.id,
                    empresa_nombre=empresa.nombre_taller,
                    event_type="nueva_suscripcion" if es_nueva_suscripcion else "renovacion",
                    provider=provider_name,
                    success=False,
                    error=str(e),
                )
            except Exception:
                pass  # No romper si falla el log de auditoría

            # Guardar registro en DB (idempotencia real) - usar idempotency_key si está disponible
            try:
                idempotency_key = WhatsAppAdminNotificationLog.generate_idempotency_key(
                    empresa_id=empresa.id,
                    event_type=event_type,
                    comprobante_pago_id=comprobante_pago_id,
                    pago_pendiente_id=pago_pendiente_id,
                    operation_uuid=operation_uuid,
                )
                _save_notification_record(
                    empresa=empresa,
                    event_type=event_type,
                    plan=plan,
                    monto=monto,
                    provider=provider_name,
                    success=False,
                    error=str(e),
                    idempotency_key=idempotency_key,
                    comprobante_pago_id=comprobante_pago_id,
                    pago_pendiente_id=pago_pendiente_id,
                )
            except Exception:
                pass  # No romper si falla el guardado

            return False
    except Exception as e:
        logger.error(
            f"Excepción inesperada en notify_admin_new_subscription: {e}",
            exc_info=True,
        )
        return False


def _save_notification_record(
    empresa,
    event_type: str,
    plan: str,
    monto: float,
    provider: str,
    success: bool,
    idempotency_key: str,
    message_id: Optional[str] = None,
    error: Optional[str] = None,
    comprobante_pago_id: Optional[int] = None,
    pago_pendiente_id: Optional[int] = None,
) -> None:
    """
    Guardar registro de notificación en DB para idempotencia real

    Args:
        empresa: Instancia de Empresa
        event_type: Tipo de evento
        plan: Plan de suscripción
        monto: Monto
        provider: Provider usado
        success: Si se envió correctamente
        idempotency_key: Clave única de idempotencia
        message_id: ID del mensaje (opcional)
        error: Mensaje de error (opcional)
        comprobante_pago_id: ID del comprobante (opcional)
        pago_pendiente_id: ID del pago pendiente (opcional)
    """
    try:
        from .models import WhatsAppAdminNotificationLog

        with transaction.atomic():
            # Usar get_or_create con idempotency_key para evitar duplicados
            notification, created = WhatsAppAdminNotificationLog.objects.get_or_create(
                idempotency_key=idempotency_key,
                defaults={
                    "empresa": empresa,
                    "event_type": event_type,
                    "plan": plan,
                    "monto": monto,
                    "provider": provider,
                    "success": success,
                    "message_id": message_id,
                    "error": error,
                    "comprobante_pago_id": comprobante_pago_id,
                    "pago_pendiente_id": pago_pendiente_id,
                },
            )

            if not created:
                # Actualizar registro existente
                notification.success = success
                notification.message_id = message_id
                notification.error = error
                notification.provider = provider
                notification.save()
    except Exception as e:
        # No romper si falla el guardado en DB
        logger.warning(f"Error guardando registro de notificación (ignorado): {e}")
