"""
Cliente para Meta Cloud API (WhatsApp Business API)
Maneja el envío de mensajes interactivos y descarga de media.
"""
import requests
from django.conf import settings
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MetaWhatsAppClient:
    """
    Cliente para interactuar con Meta Cloud API.
    """
    
    def __init__(self, phone_number_id: str, access_token: str):
        """
        Inicializar cliente con credenciales.
        
        Args:
            phone_number_id: ID del número de teléfono en Meta
            access_token: Token de acceso de Meta (desde settings.META_WA_TOKEN)
        """
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.base_url = "https://graph.facebook.com/v18.0"
    
    def send_text_message(self, to: str, message: str) -> bool:
        """
        Enviar mensaje de texto simple.
        
        Args:
            to: Número de teléfono destino (formato: 56912345678)
            message: Texto a enviar
            
        Returns:
            True si se envió correctamente, False en caso contrario
        """
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info(f"Mensaje enviado a {to}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error enviando mensaje a {to}: {e}")
            return False
    
    def send_interactive_buttons(self, to: str, message: str, buttons: list) -> bool:
        """
        Enviar mensaje con botones interactivos.
        
        Args:
            to: Número de teléfono destino
            message: Texto del mensaje
            buttons: Lista de botones [{"id": "btn1", "title": "Texto"}]
            
        Returns:
            True si se envió correctamente, False en caso contrario
        """
        if len(buttons) > 3:
            logger.warning("Máximo 3 botones permitidos, truncando lista")
            buttons = buttons[:3]
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Construir botones en formato Meta
        button_components = []
        for btn in buttons:
            button_components.append({
                "type": "reply",
                "reply": {
                    "id": btn.get("id", ""),
                    "title": btn.get("title", "")
                }
            })
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": message
                },
                "action": {
                    "buttons": button_components
                }
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info(f"Botones interactivos enviados a {to}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error enviando botones a {to}: {e}")
            return False
    
    def download_media(self, media_id: str) -> Optional[bytes]:
        """
        Descargar media (imagen, audio, video) desde Meta.
        
        Args:
            media_id: ID del media en Meta
            
        Returns:
            Bytes del archivo o None si hay error
        """
        # Primero obtener la URL del media
        url = f"{self.base_url}/{media_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            media_data = response.json()
            media_url = media_data.get("url")
            
            if not media_url:
                logger.error(f"No se encontró URL en respuesta de media {media_id}")
                return None
            
            # Descargar el archivo
            file_response = requests.get(media_url, headers=headers, timeout=30)
            file_response.raise_for_status()
            return file_response.content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error descargando media {media_id}: {e}")
            return None
