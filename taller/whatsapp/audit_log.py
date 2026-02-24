"""
Registro de auditoría para notificaciones WhatsApp admin
Opcional pero útil para debugging y soporte
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


def log_whatsapp_admin_attempt(
    empresa_id: int,
    empresa_nombre: str,
    event_type: str,  # "nueva_suscripcion" | "renovacion"
    provider: str,
    success: bool,
    error: Optional[str] = None,
    message_id: Optional[str] = None,
) -> None:
    """
    Registrar intento de envío de WhatsApp admin
    
    Args:
        empresa_id: ID de la empresa
        empresa_nombre: Nombre de la empresa
        event_type: Tipo de evento
        provider: Provider usado ("dummy" | "meta")
        success: Si se envió correctamente
        error: Mensaje de error si falló
        message_id: ID del mensaje (si se envió)
    """
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "empresa_id": empresa_id,
        "empresa_nombre": empresa_nombre,
        "event_type": event_type,
        "provider": provider,
        "success": success,
        "error": error,
        "message_id": message_id,
    }
    
    if success:
        logger.info(f"[WhatsApp Admin Audit] ✅ {event_type} - Empresa: {empresa_nombre} (ID: {empresa_id}) - Provider: {provider} - Message ID: {message_id}")
    else:
        logger.warning(f"[WhatsApp Admin Audit] ❌ {event_type} - Empresa: {empresa_nombre} (ID: {empresa_id}) - Provider: {provider} - Error: {error}")
    
    # Opcional: Guardar en DB si tienes modelo de auditoría
    # try:
    #     from taller.models.auditoria import LogAuditoria
    #     LogAuditoria.objects.create(
    #         tipo="WHATSAPP_ADMIN",
    #         descripcion=f"{event_type} - {empresa_nombre}",
    #         datos_extra=log_data,
    #     )
    # except Exception:
    #     pass  # No romper si falla el log de auditoría
