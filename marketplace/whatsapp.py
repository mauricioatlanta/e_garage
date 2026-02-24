"""
Módulo de integración con WhatsApp para eGarage
Soporta Ultramsg (Chile) y Twilio (USA/Escalabilidad)
"""
import os
import requests
from typing import Optional, Dict, Any
from django.conf import settings
from django.urls import reverse

from taller.models.documento import Documento
from taller.models.empresa import Empresa


class WhatsAppGateway:
    """
    Gateway abstracto para envío de mensajes de WhatsApp.
    Soporta múltiples proveedores (Ultramsg, Twilio).
    """
    
    def __init__(self, empresa: Empresa):
        self.empresa = empresa
        self.provider = self._get_provider()
    
    def _get_provider(self) -> str:
        """
        Determina el proveedor según el país de la empresa.
        Chile: Ultramsg (más simple)
        USA/otros: Twilio (más escalable)
        """
        pais = getattr(self.empresa, 'pais', 'CL').upper()
        return os.getenv('WHATSAPP_PROVIDER', 'ultramsg' if pais == 'CL' else 'twilio')
    
    def enviar_mensaje_cliente(
        self, 
        telefono: str, 
        documento: Documento,
        link_ver_detalle: str
    ) -> Dict[str, Any]:
        """
        Envía mensaje al cliente con link para ver su presupuesto.
        
        Template: "Su presupuesto está listo. Ver detalle aquí [LINK]"
        """
        mensaje = self._generar_mensaje_cliente(documento, link_ver_detalle)
        
        if self.provider == 'ultramsg':
            return self._enviar_ultramsg(telefono, mensaje)
        elif self.provider == 'twilio':
            return self._enviar_twilio(telefono, mensaje)
        else:
            raise ValueError(f"Proveedor de WhatsApp no soportado: {self.provider}")
    
    def enviar_mensaje_proveedor(
        self,
        telefono: str,
        documento: Documento,
        part_number: str,
        link_confirmar_stock: str
    ) -> Dict[str, Any]:
        """
        Envía mensaje al proveedor con pedido y link para confirmar stock.
        
        Template: "Pedido generado por Taller [X] para el repuesto [SKU]. 
                   Confirmar Stock: [LINK]"
        """
        mensaje = self._generar_mensaje_proveedor(
            documento, 
            part_number, 
            link_confirmar_stock
        )
        
        if self.provider == 'ultramsg':
            return self._enviar_ultramsg(telefono, mensaje)
        elif self.provider == 'twilio':
            return self._enviar_twilio(telefono, mensaje)
        else:
            raise ValueError(f"Proveedor de WhatsApp no soportado: {self.provider}")
    
    def _generar_mensaje_cliente(self, documento: Documento, link: str) -> str:
        """Genera el mensaje para el cliente"""
        tipo_doc = documento.get_tipo_display() if hasattr(documento, 'get_tipo_display') else documento.tipo
        return (
            f"✅ Su {tipo_doc} está listo.\n\n"
            f"📄 Número: {documento.numero or 'Pendiente'}\n"
            f"💰 Total: ${documento.total:,.0f}\n\n"
            f"Ver detalle completo aquí:\n{link}\n\n"
            f"Responda 'SÍ' para aprobar o 'NO' para rechazar."
        )
    
    def _generar_mensaje_proveedor(
        self, 
        documento: Documento, 
        part_number: str,
        link: str
    ) -> str:
        """Genera el mensaje para el proveedor"""
        taller_nombre = getattr(self.empresa, 'nombre_taller', 'Taller')
        return (
            f"🔧 Pedido generado por {taller_nombre}\n\n"
            f"📦 Repuesto: {part_number}\n"
            f"📄 Documento: {documento.numero or documento.id}\n\n"
            f"✅ Confirmar Stock disponible:\n{link}\n\n"
            f"Al confirmar, el taller será notificado automáticamente."
        )
    
    def _enviar_ultramsg(self, telefono: str, mensaje: str) -> Dict[str, Any]:
        """
        Envía mensaje usando Ultramsg (recomendado para Chile)
        API simple HTTP
        """
        instance_id = os.getenv('ULTRAMSG_INSTANCE_ID')
        token = os.getenv('ULTRAMSG_TOKEN')
        
        if not instance_id or not token:
            raise ValueError("Credenciales de Ultramsg no configuradas")
        
        # Formatear teléfono (agregar código de país si no tiene)
        telefono_formateado = self._formatear_telefono(telefono)
        
        url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
        payload = {
            "token": token,
            "to": telefono_formateado,
            "body": mensaje
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return {
                "success": True,
                "provider": "ultramsg",
                "message_id": response.json().get("id"),
                "response": response.json()
            }
        except requests.RequestException as e:
            return {
                "success": False,
                "provider": "ultramsg",
                "error": str(e)
            }
    
    def _enviar_twilio(self, telefono: str, mensaje: str) -> Dict[str, Any]:
        """
        Envía mensaje usando Twilio (recomendado para USA/escalabilidad)
        """
        from twilio.rest import Client
        
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        whatsapp_from = os.getenv('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
        
        if not account_sid or not auth_token:
            raise ValueError("Credenciales de Twilio no configuradas")
        
        # Formatear teléfono
        telefono_formateado = self._formatear_telefono(telefono, formato_twilio=True)
        
        try:
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                body=mensaje,
                from_=whatsapp_from,
                to=f"whatsapp:{telefono_formateado}"
            )
            return {
                "success": True,
                "provider": "twilio",
                "message_id": message.sid,
                "response": {"status": message.status}
            }
        except Exception as e:
            return {
                "success": False,
                "provider": "twilio",
                "error": str(e)
            }
    
    def _formatear_telefono(self, telefono: str, formato_twilio: bool = False) -> str:
        """
        Formatea el teléfono agregando código de país si es necesario.
        """
        # Limpiar teléfono
        telefono = telefono.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Si ya tiene código de país, retornar
        if telefono.startswith('+') or (formato_twilio and telefono.startswith('+')):
            return telefono.lstrip('+')
        
        # Agregar código según país de la empresa
        pais = getattr(self.empresa, 'pais', 'CL').upper()
        if pais == 'CL':
            # Chile: +56
            if not telefono.startswith('56'):
                telefono = '56' + telefono.lstrip('0')
        elif pais == 'US':
            # USA: +1
            if not telefono.startswith('1'):
                telefono = '1' + telefono
        
        return telefono
    
    @staticmethod
    def procesar_respuesta_cliente(mensaje: str) -> Optional[str]:
        """
        Procesa la respuesta del cliente y determina si aprobó o rechazó.
        Retorna: 'APROBADO', 'RECHAZADO', o None si no se puede determinar
        """
        mensaje_lower = mensaje.lower().strip()
        
        # Palabras de aprobación
        aprobacion = ['sí', 'si', 'yes', 'ok', 'aprobado', 'acepto', 'confirmo', 'de acuerdo']
        # Palabras de rechazo
        rechazo = ['no', 'rechazo', 'rechazado', 'cancelar', 'cancelado']
        
        if any(palabra in mensaje_lower for palabra in aprobacion):
            return 'APROBADO'
        elif any(palabra in mensaje_lower for palabra in rechazo):
            return 'RECHAZADO'
        
        return None
