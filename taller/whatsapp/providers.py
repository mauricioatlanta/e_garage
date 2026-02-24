"""
Providers de WhatsApp para notificaciones admin
Soporta: dummy (tests/dev) y meta (producción)
"""
import logging
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class WhatsAppProvider:
    """Provider base abstracto"""
    
    def send(self, to: str, message: str) -> Dict[str, Any]:
        """
        Enviar mensaje de WhatsApp
        
        Args:
            to: Número de teléfono destino (formato E.164: +56912345678)
            message: Mensaje a enviar
            
        Returns:
            Dict con success, provider, message_id (opcional), error (opcional)
        """
        raise NotImplementedError


class DummyWhatsAppProvider(WhatsAppProvider):
    """Provider dummy para tests/dev - solo loggea, no envía"""
    
    def send(self, to: str, message: str) -> Dict[str, Any]:
        """Loggea el mensaje sin enviarlo"""
        logger.info(f"[DUMMY WhatsApp] Enviando a {to}:")
        logger.info(f"[DUMMY WhatsApp] Mensaje: {message}")
        return {
            "success": True,
            "provider": "dummy",
            "message_id": f"dummy_{to}_{hash(message)}",
        }


class MetaWhatsAppProvider(WhatsAppProvider):
    """Provider para Meta Cloud API (WhatsApp Business API)"""
    
    def __init__(self, phone_number_id: Optional[str] = None, access_token: Optional[str] = None):
        """
        Inicializar provider con credenciales
        
        Args:
            phone_number_id: ID del número de teléfono en Meta (desde env o settings)
            access_token: Token de acceso de Meta (desde env o settings)
        """
        self.phone_number_id = phone_number_id or getattr(
            settings, "WHATSAPP_ADMIN_PHONE_NUMBER_ID", None
        )
        self.access_token = access_token or getattr(
            settings, "WHATSAPP_ADMIN_ACCESS_TOKEN", None
        )
        self.base_url = "https://graph.facebook.com/v18.0"
        
        if not self.phone_number_id or not self.access_token:
            logger.warning(
                "MetaWhatsAppProvider: Credenciales no configuradas. "
                "Usar WHATSAPP_ADMIN_PHONE_NUMBER_ID y WHATSAPP_ADMIN_ACCESS_TOKEN en settings/env"
            )
    
    def send(self, to: str, message: str) -> Dict[str, Any]:
        """
        Enviar mensaje usando Meta Cloud API
        
        Args:
            to: Número de teléfono destino (formato E.164: +56912345678)
            message: Mensaje a enviar
            
        Returns:
            Dict con success, provider, message_id (opcional), error (opcional)
        """
        if not self.phone_number_id or not self.access_token:
            logger.error("MetaWhatsAppProvider: Credenciales no configuradas")
            return {
                "success": False,
                "provider": "meta",
                "error": "Credenciales no configuradas",
            }
        
        # Limpiar número (remover +, espacios, guiones)
        to_clean = to.replace("+", "").replace(" ", "").replace("-", "")
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_clean,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message,
            },
        }
        
        try:
            import requests
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            response_data = response.json()
            message_id = response_data.get("messages", [{}])[0].get("id", None)
            
            logger.info(f"MetaWhatsAppProvider: Mensaje enviado a {to} (ID: {message_id})")
            return {
                "success": True,
                "provider": "meta",
                "message_id": message_id,
            }
        except Exception as e:
            logger.error(f"MetaWhatsAppProvider: Error enviando a {to}: {e}")
            return {
                "success": False,
                "provider": "meta",
                "error": str(e),
            }


def get_whatsapp_provider() -> WhatsAppProvider:
    """
    Obtener provider de WhatsApp según configuración
    
    Returns:
        Instancia de WhatsAppProvider (DummyWhatsAppProvider o MetaWhatsAppProvider)
    """
    provider_name = getattr(settings, "WHATSAPP_ADMIN_PROVIDER", "dummy").lower()
    enabled = getattr(settings, "WHATSAPP_ADMIN_NOTIFICATIONS_ENABLED", False)
    
    # En tests/dev, forzar dummy si no está explícitamente habilitado
    if not enabled:
        logger.debug("WhatsApp admin notifications disabled, using dummy provider")
        return DummyWhatsAppProvider()
    
    if provider_name == "meta":
        return MetaWhatsAppProvider()
    else:
        # Default: dummy
        return DummyWhatsAppProvider()
