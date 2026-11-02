"""
Máquina de Estados - El cerebro del flujo conversacional
Gestiona el estado de la conversación y procesa los mensajes según el estado actual.
"""

from typing import Optional, Dict, Any
from django.utils import timezone
import logging

from ..models import WhatsAppSession
from .meta import MetaWhatsAppClient
from .nlp import NLPProcessor

logger = logging.getLogger(__name__)


class WhatsAppFlowManager:
    """
    Gestor del flujo conversacional de WhatsApp.
    Implementa la máquina de estados para el proceso de ingreso de vehículos.
    """

    def __init__(self, session: WhatsAppSession, meta_client: MetaWhatsAppClient):
        """
        Inicializar gestor de flujo.

        Args:
            session: Sesión activa de WhatsApp
            meta_client: Cliente de Meta API
        """
        self.session = session
        self.meta_client = meta_client
        self.nlp = NLPProcessor()
        self.ocr = None  # OCR deshabilitado

    def process_message(self, from_phone: str, message_type: str, content: Any) -> bool:
        """
        Procesar mensaje entrante según el estado actual.

        Args:
            from_phone: Teléfono del remitente
            message_type: Tipo de mensaje (text, image, audio, etc.)
            content: Contenido del mensaje

        Returns:
            True si se procesó correctamente
        """
        # Verificar si la sesión expiró
        if self.session.is_expired():
            self.session.reset()
            self.meta_client.send_text_message(
                from_phone, "⏱ Tu sesión expiró. Escribe 'Nuevo' o '🆕' para comenzar."
            )
            return False

        # Actualizar última interacción
        self.session.last_interaction = timezone.now()

        # Procesar según estado
        if self.session.estado == "IDLE":
            return self._handle_idle(from_phone, message_type, content)
        elif self.session.estado == "WAITING_PLATE":
            return self._handle_waiting_plate(from_phone, message_type, content)
        elif self.session.estado == "WAITING_MILEAGE":
            return self._handle_waiting_mileage(from_phone, message_type, content)
        elif self.session.estado == "WAITING_ACTION":
            return self._handle_waiting_action(from_phone, message_type, content)
        elif self.session.estado == "WAITING_CONFIRM":
            return self._handle_waiting_confirm(from_phone, message_type, content)
        else:
            logger.warning(f"Estado desconocido: {self.session.estado}")
            return False

    def _handle_idle(self, from_phone: str, message_type: str, content: Any) -> bool:
        """Manejar estado IDLE - esperando comando inicial"""
        if message_type == "text":
            text = content.get("text", "").strip()
            text_lower = text.lower()

            # Comandos especiales
            if text_lower in ["nuevo", "🆕", "nueva", "nuevo vehiculo"]:
                self.session.estado = "WAITING_PLATE"
                self.session.save()
                self.meta_client.send_text_message(
                    from_phone, "📸 *Nuevo Vehículo*\n\nEnvía una foto de la patente para comenzar."
                )
                return True
            elif text_lower in ["cancelar", "cancel", "salir"]:
                self.session.reset()
                self.meta_client.send_text_message(
                    from_phone, "❌ Operación cancelada. Escribe 'Nuevo' para comenzar."
                )
                return True
            else:
                # Procesar texto con NLP
                result = self.nlp.process_text(text)
                return self._handle_nlp_result(from_phone, result)
        return False

    def _handle_waiting_plate(self, from_phone: str, message_type: str, content: Any) -> bool:
        """Manejar estado WAITING_PLATE - esperando foto de patente"""
        if message_type == "image":
            media_id = content.get("id")
            if not media_id:
                self.meta_client.send_text_message(
                    from_phone, "❌ No se pudo obtener la imagen. Intenta nuevamente."
                )
                return False

            # Descargar imagen
            image_bytes = self.meta_client.download_media(media_id)
            if not image_bytes:
                self.meta_client.send_text_message(
                    from_phone, "❌ Error descargando imagen. Intenta nuevamente."
                )
                return False

            if not self.ocr:
                self.meta_client.send_text_message(
                    from_phone,
                    "❌ OCR deshabilitado temporalmente. Por favor, ingresa la patente manualmente.",
                )
                return False
            # Procesar OCR
            patente = self.ocr.extract_plate(image_bytes)
            if not patente:
                self.meta_client.send_text_message(
                    from_phone,
                    "❌ No se pudo leer la patente. Por favor, envía una foto más clara.",
                )
                return False

            # Buscar o crear vehículo
            # TODO: Implementar lógica de búsqueda/creación de vehículo
            # Por ahora, solo avanzamos al siguiente estado
            self.session.contexto["patente"] = patente
            self.session.estado = "WAITING_MILEAGE"
            self.session.save()

            self.meta_client.send_text_message(
                from_phone,
                f"✅ Patente detectada: *{patente}*\n\n📊 ¿Cuál es el kilometraje actual?",
            )
            return True
        else:
            self.meta_client.send_text_message(
                from_phone, "📸 Por favor, envía una foto de la patente."
            )
            return False

    def _handle_waiting_mileage(self, from_phone: str, message_type: str, content: Any) -> bool:
        """Manejar estado WAITING_MILEAGE - esperando kilometraje"""
        if message_type == "text":
            text = content.get("text", "").strip()
            try:
                kilometraje = int(text.replace(".", "").replace(",", ""))
                if kilometraje < 0 or kilometraje > 9999999:
                    raise ValueError("Kilometraje fuera de rango")

                self.session.contexto["kilometraje"] = kilometraje
                self.session.estado = "WAITING_ACTION"
                self.session.save()

                # Mostrar menú de acciones
                buttons = [
                    {"id": "servicio", "title": "🛠 Servicio"},
                    {"id": "repuesto", "title": "🔩 Repuesto"},
                    {"id": "externo", "title": "🏢 Externo"},
                    {"id": "evidencia", "title": "📸 Evidencia"},
                    {"id": "finalizar", "title": "✅ Finalizar"},
                ]

                self.meta_client.send_interactive_buttons(
                    from_phone,
                    f"✅ Kilometraje registrado: *{kilometraje:,} km*\n\n¿Qué deseas hacer?",
                    buttons,
                )
                return True
            except ValueError:
                self.meta_client.send_text_message(
                    from_phone, "❌ Por favor, envía un número válido de kilometraje (ej: 50000)."
                )
                return False
        else:
            self.meta_client.send_text_message(
                from_phone, "📊 Por favor, envía el kilometraje como número (ej: 50000)."
            )
            return False

    def _handle_waiting_action(self, from_phone: str, message_type: str, content: Any) -> bool:
        """Manejar estado WAITING_ACTION - esperando acción del menú"""
        if message_type == "interactive":
            button_id = content.get("button_reply", {}).get("id")
            if button_id == "finalizar":
                # TODO: Finalizar OT
                self.meta_client.send_text_message(
                    from_phone, "✅ Orden de Trabajo finalizada correctamente."
                )
                self.session.reset()
                return True
            elif button_id in ["servicio", "repuesto", "externo"]:
                self.meta_client.send_text_message(
                    from_phone,
                    f"📝 Procesando {button_id}...\n\nEnvía un audio o texto con los detalles.",
                )
                # TODO: Implementar procesamiento de servicios/repuestos
                return True
            elif button_id == "evidencia":
                self.meta_client.send_text_message(
                    from_phone, "📸 Envía una foto o video como evidencia."
                )
                # TODO: Implementar asociación de evidencia
                return True
        elif message_type in ["image", "video"]:
            # Evidencia automática
            # TODO: Implementar asociación automática al documento
            self.meta_client.send_text_message(from_phone, "✅ Evidencia registrada correctamente.")
            return True
        elif message_type == "audio":
            # Procesar audio con NLP
            media_id = content.get("id")
            if not media_id:
                self.meta_client.send_text_message(
                    from_phone, "❌ No se pudo obtener el audio. Intenta nuevamente."
                )
                return False

            # Descargar audio
            audio_bytes = self.meta_client.download_media(media_id)
            if not audio_bytes:
                self.meta_client.send_text_message(
                    from_phone, "❌ Error descargando audio. Intenta nuevamente."
                )
                return False

            # Procesar con NLP
            self.meta_client.send_text_message(from_phone, "🎤 Procesando audio...")

            result = self.nlp.process_audio(audio_bytes, mime_type="audio/ogg")
            return self._handle_nlp_result(from_phone, result)

        return False

    def _handle_waiting_confirm(self, from_phone: str, message_type: str, content: Any) -> bool:
        """Manejar estado WAITING_CONFIRM - esperando confirmación"""
        # TODO: Implementar lógica de confirmación
        return False

    def _handle_nlp_result(self, from_phone: str, result: Optional[Dict[str, Any]]) -> bool:
        """
        Manejar resultado del procesamiento NLP.

        Args:
            from_phone: Teléfono del remitente
            result: Resultado del NLP o None si hubo error o confidence bajo

        Returns:
            True si se procesó correctamente
        """
        if not result:
            # Confidence bajo o error - mostrar botones de modo manual
            buttons = [
                {"id": "manual_servicio", "title": "🛠 Agregar Servicio"},
                {"id": "manual_repuesto", "title": "🔩 Agregar Repuesto"},
                {"id": "manual_externo", "title": "🏢 Servicio Externo"},
                {"id": "cancelar", "title": "❌ Cancelar"},
            ]
            self.meta_client.send_interactive_buttons(
                from_phone,
                "⚠️ No pude entender el mensaje con suficiente confianza.\n\nPor favor, selecciona una opción:",
                buttons,
            )
            return False

        action = result.get("action")
        data = result.get("data", {})
        confidence = result.get("confidence", 0.0)

        logger.info(f"Procesando acción NLP: {action} (confidence: {confidence})")

        # Procesar según acción
        if action == "CREATE_OT":
            return self._process_create_ot(from_phone, data)
        elif action == "ADD_SERVICE":
            return self._process_add_service(from_phone, data)
        elif action == "ADD_PART":
            return self._process_add_part(from_phone, data)
        elif action == "ADD_OUTSOURCED":
            return self._process_add_outsourced(from_phone, data)
        elif action == "GET_SUMMARY":
            return self._process_get_summary(from_phone, data)
        else:
            logger.warning(f"Acción desconocida: {action}")
            self.meta_client.send_text_message(
                from_phone, f"❌ Acción '{action}' no reconocida. Intenta nuevamente."
            )
            return False

    def _process_create_ot(self, from_phone: str, data: Dict[str, Any]) -> bool:
        """Procesar creación de OT desde NLP"""
        # TODO: Implementar creación real de OT
        patente = data.get("patente")
        cliente = data.get("cliente_nombre")
        servicios = data.get("servicios", [])

        mensaje = f"✅ *Orden de Trabajo*\n\n"
        if patente:
            mensaje += f"Patente: *{patente}*\n"
        if cliente:
            mensaje += f"Cliente: *{cliente}*\n"
        if servicios:
            mensaje += f"\nServicios:\n"
            for srv in servicios:
                nombre = srv.get("nombre", "")
                precio = srv.get("precio")
                if precio:
                    mensaje += f"• {nombre}: ${precio:,.0f}\n"
                else:
                    mensaje += f"• {nombre}\n"

        mensaje += "\n⚠️ Funcionalidad en desarrollo"
        self.meta_client.send_text_message(from_phone, mensaje)
        return True

    def _process_add_service(self, from_phone: str, data: Dict[str, Any]) -> bool:
        """Procesar agregar servicio desde NLP"""
        servicios = data.get("servicios", [])
        if not servicios:
            self.meta_client.send_text_message(
                from_phone, "❌ No se encontraron servicios en el mensaje."
            )
            return False

        # TODO: Implementar agregar servicio real al documento
        mensaje = "✅ *Servicios agregados:*\n\n"
        for srv in servicios:
            nombre = srv.get("nombre", "")
            precio = srv.get("precio")
            if precio:
                mensaje += f"• {nombre}: ${precio:,.0f}\n"
            else:
                mensaje += f"• {nombre}\n"

        mensaje += "\n⚠️ Funcionalidad en desarrollo"
        self.meta_client.send_text_message(from_phone, mensaje)
        return True

    def _process_add_part(self, from_phone: str, data: Dict[str, Any]) -> bool:
        """Procesar agregar repuesto desde NLP"""
        repuestos = data.get("repuestos", [])
        if not repuestos:
            self.meta_client.send_text_message(
                from_phone, "❌ No se encontraron repuestos en el mensaje."
            )
            return False

        # TODO: Implementar agregar repuesto real al documento
        mensaje = "✅ *Repuestos agregados:*\n\n"
        for rep in repuestos:
            nombre = rep.get("nombre", "")
            cantidad = rep.get("cantidad", 1)
            precio = rep.get("precio")
            if precio:
                mensaje += f"• {nombre} (x{cantidad}): ${precio:,.0f}\n"
            else:
                mensaje += f"• {nombre} (x{cantidad})\n"

        mensaje += "\n⚠️ Funcionalidad en desarrollo"
        self.meta_client.send_text_message(from_phone, mensaje)
        return True

    def _process_add_outsourced(self, from_phone: str, data: Dict[str, Any]) -> bool:
        """Procesar agregar servicio externo desde NLP"""
        externos = data.get("outsourced", [])
        if not externos:
            self.meta_client.send_text_message(
                from_phone, "❌ No se encontraron servicios externos en el mensaje."
            )
            return False

        # TODO: Implementar agregar servicio externo real
        mensaje = "✅ *Servicios externos agregados:*\n\n"
        for ext in externos:
            empresa = ext.get("empresa", "")
            servicio = ext.get("servicio", "")
            costo = ext.get("costo")
            precio_cliente = ext.get("precio_cliente")
            mensaje += f"• {servicio} - {empresa}\n"
            if costo and precio_cliente:
                mensaje += f"  Costo: ${costo:,.0f} | Cliente: ${precio_cliente:,.0f}\n"

        mensaje += "\n⚠️ Funcionalidad en desarrollo"
        self.meta_client.send_text_message(from_phone, mensaje)
        return True

    def _process_get_summary(self, from_phone: str, data: Dict[str, Any]) -> bool:
        """Procesar solicitud de resumen desde NLP"""
        # TODO: Implementar cálculo real de resumen del día
        mensaje = "📊 *Resumen del día*\n\n"
        mensaje += "⚠️ Funcionalidad en desarrollo\n\n"
        mensaje += "Próximamente podrás ver:\n"
        mensaje += "• Total de OTs del día\n"
        mensaje += "• Ingresos totales\n"
        mensaje += "• Servicios realizados"

        self.meta_client.send_text_message(from_phone, mensaje)
        return True
