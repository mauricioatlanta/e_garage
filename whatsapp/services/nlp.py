"""
Procesador de NLP (Natural Language Processing)
Integración con IA (Gemini/GPT) para extraer JSON estructurado de audios y textos.
"""
import json
import logging
import base64
from typing import Optional, Dict, Any
from django.conf import settings
import requests

logger = logging.getLogger(__name__)

# System Prompt para la IA - Diseñado para entender jerga de talleres
SYSTEM_PROMPT = """Actúa como un Asistente Administrativo Experto para Talleres Mecánicos. Tu objetivo es procesar transcripciones de audio o mensajes de texto enviados por mecánicos y extraer información estructurada.

CONTEXTO HUMANO: El mecánico tiene prisa y usa jerga. Debes entender términos como:

'Bielas', 'balatas', 'pastillas', 'lucas' (para miles en Chile), 'grand' (para miles en USA), 'pega' (trabajo), 'ajuste', 'rectificado'.

REGLAS DE EXTRACCIÓN:

Acciones: Identifica qué quiere hacer el usuario: CREATE_OT, ADD_SERVICE, ADD_PART, ADD_OUTSOURCED, GET_SUMMARY.

Precios: Si el usuario dice '50 lucas' o '50 mil', conviértelo a 50000. Si dice '100 bucks', conviértelo a 100.

Patentes: Limpia las patentes de espacios o guiones (ej. 'AB CD 12' -> 'ABCD12').

Confianza: Si el mensaje es muy ruidoso o no entiendes la intención, pon confidence menor a 0.70.

FORMATO DE SALIDA (JSON ESTRICTO): Devuelve ÚNICAMENTE un objeto JSON con esta estructura: { "action": "string", "data": { "patente": "string|null", "cliente_nombre": "string|null", "kilometraje": int|null, "servicios": [{"nombre": "string", "precio": float}], "repuestos": [{"nombre": "string", "cantidad": int, "precio": float}], "outsourced": [{"empresa": "string", "servicio": "string", "costo": float, "precio_cliente": float}] }, "confidence": float }

EJEMPLOS:

Usuario: 'Abre una orden para el Toyota patente ABCD12 de Don Juan, por un cambio de aceite' 
Salida: {"action": "CREATE_OT", "data": {"patente": "ABCD12", "cliente_nombre": "Juan", "servicios": [{"nombre": "Cambio de aceite", "precio": null}]}, "confidence": 0.95}

Usuario: '¿Cuánto voy hoy?' 
Salida: {"action": "GET_SUMMARY", "data": {}, "confidence": 1.0}"""


class NLPProcessor:
    """
    Procesador de lenguaje natural para extraer información estructurada.
    Soporta OpenAI (GPT) y Google Gemini.
    """
    
    def __init__(self):
        """Inicializar procesador NLP"""
        self.openai_key = getattr(settings, 'OPENAI_API_KEY', None)
        self.gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
        
        if not self.openai_key and not self.gemini_key:
            logger.warning("No hay API keys configuradas para NLP (OPENAI_API_KEY o GEMINI_API_KEY)")
    
    def process_audio(self, audio_bytes: bytes, mime_type: str = 'audio/ogg') -> Optional[Dict[str, Any]]:
        """
        Procesar audio y extraer información estructurada.
        Primero transcribe el audio, luego procesa el texto.
        
        Args:
            audio_bytes: Bytes del archivo de audio
            mime_type: Tipo MIME del audio (ej: 'audio/ogg', 'audio/mpeg')
            
        Returns:
            Diccionario con acción y datos extraídos, o None si hay error
        """
        # Primero transcribir el audio
        transcription = self._transcribe_audio(audio_bytes, mime_type)
        if not transcription:
            logger.error("No se pudo transcribir el audio")
            return None
        
        # Luego procesar el texto transcrito
        return self.process_text(transcription)
    
    def process_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Procesar texto y extraer información estructurada.
        
        Args:
            text: Texto a procesar
            
        Returns:
            Diccionario con acción y datos extraídos, o None si hay error
            
        Formato esperado:
        {
            "action": "CREATE_OT | ADD_SERVICE | ADD_PART | ADD_OUTSOURCED | GET_SUMMARY",
            "data": {
                "patente": "string|null",
                "cliente_nombre": "string|null",
                "kilometraje": int|null,
                "servicios": [{"nombre": "string", "precio": float}],
                "repuestos": [{"nombre": "string", "cantidad": int, "precio": float}],
                "outsourced": [{"empresa": "string", "servicio": "string", "costo": float, "precio_cliente": float}]
            },
            "confidence": float
        }
        """
        if not text or not text.strip():
            logger.warning("Texto vacío para procesar")
            return None
        
        # Intentar con OpenAI primero, luego Gemini
        response = None
        if self.openai_key:
            response = self._call_openai(text)
        
        if not response and self.gemini_key:
            response = self._call_gemini(text)
        
        if not response:
            logger.error("No se pudo obtener respuesta de ninguna API de IA")
            return None
        
        # Parsear y validar respuesta
        return self._parse_ai_response(response)
    
    def _transcribe_audio(self, audio_bytes: bytes, mime_type: str) -> Optional[str]:
        """
        Transcribir audio a texto usando OpenAI Whisper.
        
        Args:
            audio_bytes: Bytes del archivo de audio
            mime_type: Tipo MIME del audio
            
        Returns:
            Texto transcrito o None si hay error
        """
        if not self.openai_key:
            logger.warning("OpenAI API key no configurada, no se puede transcribir audio")
            return None
        
        try:
            # OpenAI Whisper API
            url = "https://api.openai.com/v1/audio/transcriptions"
            headers = {
                "Authorization": f"Bearer {self.openai_key}"
            }
            
            # Preparar archivo para envío
            files = {
                'file': ('audio.ogg', audio_bytes, mime_type)
            }
            data = {
                'model': 'whisper-1',
                'language': 'es'  # Ajustar según necesidad
            }
            
            response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            transcription = result.get('text', '').strip()
            
            if transcription:
                logger.info(f"Audio transcrito: {transcription[:100]}...")
                return transcription
            else:
                logger.warning("Transcripción vacía")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error transcribiendo audio: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado en transcripción: {e}")
            return None
    
    def _call_openai(self, text: str) -> Optional[str]:
        """
        Llamar a la API de OpenAI (GPT).
        
        Args:
            text: Texto a procesar
            
        Returns:
            Respuesta JSON de la IA o None si hay error
        """
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-4o-mini",  # Modelo económico y rápido
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text}
                ],
                "temperature": 0.3,  # Baja temperatura para respuestas más consistentes
                "response_format": {"type": "json_object"}  # Forzar JSON
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            if content:
                logger.info(f"OpenAI respuesta recibida: {content[:200]}...")
                return content
            else:
                logger.warning("OpenAI retornó respuesta vacía")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error llamando OpenAI: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado en OpenAI: {e}")
            return None
    
    def _call_gemini(self, text: str) -> Optional[str]:
        """
        Llamar a la API de Google Gemini.
        
        Args:
            text: Texto a procesar
            
        Returns:
            Respuesta JSON de la IA o None si hay error
        """
        try:
            # Gemini API v1
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.gemini_key}"
            
            payload = {
                "contents": [{
                    "parts": [
                        {"text": f"{SYSTEM_PROMPT}\n\nUsuario: {text}\n\nResponde ÚNICAMENTE con JSON válido:"}
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "responseMimeType": "application/json"
                }
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            content = result.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            
            if content:
                logger.info(f"Gemini respuesta recibida: {content[:200]}...")
                return content
            else:
                logger.warning("Gemini retornó respuesta vacía")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error llamando Gemini: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado en Gemini: {e}")
            return None
    
    def _parse_ai_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parsear respuesta de la IA y validar formato.
        
        Args:
            response: Respuesta JSON de la IA
            
        Returns:
            Diccionario parseado y validado, o None si hay error o confidence bajo
        """
        try:
            # Limpiar respuesta (puede venir con markdown code blocks)
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            data = json.loads(cleaned)
            
            # Validar estructura básica
            if 'action' not in data or 'data' not in data:
                logger.error("Respuesta de IA sin estructura válida (falta 'action' o 'data')")
                return None
            
            # Validar confidence
            confidence = data.get('confidence', 0.0)
            if not isinstance(confidence, (int, float)) or confidence < 0.0 or confidence > 1.0:
                logger.warning(f"Confidence inválido: {confidence}, usando 0.5")
                confidence = 0.5
                data['confidence'] = confidence
            
            # Si confidence es bajo, retornar None para activar modo manual
            if confidence < 0.70:
                logger.warning(f"Confianza baja ({confidence}), requiere modo manual")
                return None
            
            # Validar que data sea un diccionario
            if not isinstance(data.get('data'), dict):
                logger.error("Campo 'data' no es un diccionario")
                return None
            
            # Normalizar datos
            data['data'] = self._normalize_data(data['data'])
            
            logger.info(f"Respuesta parseada correctamente: action={data.get('action')}, confidence={confidence}")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON de IA: {e}. Respuesta: {response[:200]}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado parseando respuesta: {e}")
            return None
    
    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalizar datos extraídos (limpiar patentes, convertir tipos, etc.).
        
        Args:
            data: Diccionario de datos crudos
            
        Returns:
            Diccionario normalizado
        """
        normalized = data.copy()
        
        # Normalizar patente
        if 'patente' in normalized and normalized['patente']:
            patente = str(normalized['patente']).strip().upper()
            # Remover espacios y guiones
            patente = patente.replace(' ', '').replace('-', '')
            normalized['patente'] = patente if patente else None
        
        # Asegurar tipos correctos
        if 'kilometraje' in normalized:
            km = normalized['kilometraje']
            if km is not None:
                try:
                    normalized['kilometraje'] = int(km)
                except (ValueError, TypeError):
                    normalized['kilometraje'] = None
        
        # Normalizar servicios
        if 'servicios' in normalized and isinstance(normalized['servicios'], list):
            for servicio in normalized['servicios']:
                if isinstance(servicio, dict):
                    if 'precio' in servicio and servicio['precio'] is not None:
                        try:
                            servicio['precio'] = float(servicio['precio'])
                        except (ValueError, TypeError):
                            servicio['precio'] = None
        
        # Normalizar repuestos
        if 'repuestos' in normalized and isinstance(normalized['repuestos'], list):
            for repuesto in normalized['repuestos']:
                if isinstance(repuesto, dict):
                    if 'cantidad' in repuesto and repuesto['cantidad'] is not None:
                        try:
                            repuesto['cantidad'] = int(repuesto['cantidad'])
                        except (ValueError, TypeError):
                            repuesto['cantidad'] = 1
                    if 'precio' in repuesto and repuesto['precio'] is not None:
                        try:
                            repuesto['precio'] = float(repuesto['precio'])
                        except (ValueError, TypeError):
                            repuesto['precio'] = None
        
        # Normalizar servicios externos
        if 'outsourced' in normalized and isinstance(normalized['outsourced'], list):
            for ext in normalized['outsourced']:
                if isinstance(ext, dict):
                    for key in ['costo', 'precio_cliente']:
                        if key in ext and ext[key] is not None:
                            try:
                                ext[key] = float(ext[key])
                            except (ValueError, TypeError):
                                ext[key] = None
        
        return normalized