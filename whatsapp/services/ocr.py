"""
Procesador OCR (Optical Character Recognition)
Reconocimiento de patentes desde imágenes usando EasyOCR (Open Source).
"""

import logging
import re
from typing import Optional, Dict, Any

from django.conf import settings
import numpy as np

logger = logging.getLogger(__name__)

# Feature flag: solo intentamos usar EasyOCR si está activado explícitamente
OCR_ENABLED = getattr(settings, "EGARAGE_ENABLE_OCR", False)

if OCR_ENABLED:
    # Intentar importar EasyOCR y OpenCV solo cuando la funcionalidad está habilitada
    try:
        import easyocr
        import cv2

        EASYOCR_AVAILABLE = True
    except ImportError:
        EASYOCR_AVAILABLE = False
        # Aquí sí registramos aviso porque el admin activó OCR pero falta instalar el paquete
        logger.warning(
            "OCR habilitado (EGARAGE_ENABLE_OCR=True) pero EasyOCR/OpenCV no están instalados. "
            "Ejecuta: pip install easyocr opencv-python-headless"
        )
else:
    # OCR desactivado: no intentamos importar ni mostramos warnings ruidosos
    EASYOCR_AVAILABLE = False


# Singleton global para el Reader de EasyOCR (optimización de memoria)
_READER_INSTANCE = None
_READER_LANGUAGES = None
_READER_GPU = None


def get_reader(languages=None, gpu=False):
    """
    Obtener instancia singleton del Reader de EasyOCR.
    Solo se inicializa una vez para ahorrar memoria.

    Args:
        languages: Lista de idiomas. Si cambia, se reinicializa
        gpu: Usar GPU. Si cambia, se reinicializa

    Returns:
        Instancia de easyocr.Reader o None si hay error
    """
    global _READER_INSTANCE, _READER_LANGUAGES, _READER_GPU

    if not EASYOCR_AVAILABLE:
        return None

    languages = languages or ["es", "en"]

    # Reinicializar si cambian los parámetros
    if _READER_INSTANCE is None or _READER_LANGUAGES != languages or _READER_GPU != gpu:

        try:
            logger.info(
                f"Inicializando EasyOCR Reader (Singleton) - idiomas: {languages}, GPU: {gpu}"
            )
            _READER_INSTANCE = easyocr.Reader(languages, gpu=gpu)
            _READER_LANGUAGES = languages
            _READER_GPU = gpu
            logger.info("EasyOCR Reader inicializado correctamente (Singleton)")
        except Exception as e:
            logger.error(f"Error inicializando EasyOCR Reader: {e}", exc_info=True)
            _READER_INSTANCE = None

    return _READER_INSTANCE


class OCRProcessor:
    """
    Procesador OCR para extraer texto de imágenes (principalmente patentes).
    Usa EasyOCR (Open Source) con soporte para múltiples países.
    """

    # Threshold de confianza mínimo (0.0 a 1.0)
    CONFIDENCE_THRESHOLD = 0.6

    def __init__(self, languages=None, gpu=False, confidence_threshold=0.6):
        """
        Inicializar procesador OCR con EasyOCR.

        Args:
            languages: Lista de idiomas (ej: ['es', 'en']). Default: ['es']
            gpu: Usar GPU si está disponible. Default: False
            confidence_threshold: Confianza mínima aceptable (0.0-1.0). Default: 0.6
        """
        self.languages = languages or ["es", "en"]
        self.gpu = gpu
        self.CONFIDENCE_THRESHOLD = confidence_threshold

        if not EASYOCR_AVAILABLE:
            logger.error(
                "EasyOCR no está disponible. Ejecuta: pip install easyocr opencv-python-headless"
            )

    def extract_plate(
        self, image_bytes: bytes, return_full_result: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Extraer patente de una imagen usando EasyOCR con validación de confianza.

        Args:
            image_bytes: Bytes de la imagen
            return_full_result: Si True, retorna dict completo con detalles

        Returns:
            Si return_full_result=False: string con patente o None
            Si return_full_result=True: dict con {
                'plate': str,           # Patente detectada (mejor candidato)
                'confidence': float,    # Confianza del mejor candidato (0.0-1.0)
                'needs_manual_confirm': bool,  # True si confianza < threshold
                'candidates': [         # Lista de todos los candidatos válidos
                    {'plate': str, 'confidence': float, 'country': str}
                ]
            }
        """
        if not image_bytes:
            logger.error("Imagen vacía")
            return (
                None
                if not return_full_result
                else {
                    "plate": None,
                    "confidence": 0.0,
                    "needs_manual_confirm": True,
                    "candidates": [],
                }
            )

        reader = get_reader(self.languages, self.gpu)
        if reader is None:
            logger.error("EasyOCR Reader no está disponible")
            return (
                None
                if not return_full_result
                else {
                    "plate": None,
                    "confidence": 0.0,
                    "needs_manual_confirm": True,
                    "candidates": [],
                }
            )

        try:
            # 1. Convertir bytes a imagen OpenCV
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                logger.error("No se pudo decodificar la imagen")
                return (
                    None
                    if not return_full_result
                    else {
                        "plate": None,
                        "confidence": 0.0,
                        "needs_manual_confirm": True,
                        "candidates": [],
                    }
                )

            # 2. Pre-procesamiento opcional para mejorar detección
            img_processed = self._preprocess_image(img)

            # 3. OCR: Extraer texto con detalles (incluyendo confianza)
            # detail=1 retorna: [[bbox, text, confidence], ...]
            results = reader.readtext(img_processed, detail=1)

            if not results:
                logger.warning("EasyOCR no detectó texto en la imagen")
                return (
                    None
                    if not return_full_result
                    else {
                        "plate": None,
                        "confidence": 0.0,
                        "needs_manual_confirm": True,
                        "candidates": [],
                    }
                )

            # 4. Extraer todos los textos detectados con sus confianzas
            all_texts = []
            for bbox, text, confidence in results:
                all_texts.append({"text": text.upper().strip(), "confidence": float(confidence)})

            raw_text = " ".join([item["text"] for item in all_texts])
            logger.debug(f"Texto crudo detectado por EasyOCR: {raw_text}")

            # 5. Buscar todas las patentes posibles en el texto (múltiples candidatos)
            candidates = self._find_all_plates_in_text(all_texts)

            if not candidates:
                logger.warning(f"No se encontraron patentes válidas en: {raw_text}")
                return (
                    None
                    if not return_full_result
                    else {
                        "plate": None,
                        "confidence": 0.0,
                        "needs_manual_confirm": True,
                        "candidates": [],
                    }
                )

            # 6. Ordenar candidatos: primero por regex match (país específico), luego por confianza
            candidates = self._prioritize_candidates(candidates)

            # 7. Mejor candidato es el primero (mayor prioridad)
            best_candidate = candidates[0]
            best_confidence = best_candidate["confidence"]

            # 8. Determinar si necesita confirmación manual
            needs_confirm = best_confidence < self.CONFIDENCE_THRESHOLD

            result = {
                "plate": best_candidate["plate"],
                "confidence": best_confidence,
                "needs_manual_confirm": needs_confirm,
                "candidates": candidates,
            }

            if needs_confirm:
                logger.warning(
                    f"Confianza baja ({best_confidence:.2f}) - requiere confirmación manual: {best_candidate['plate']}"
                )
            else:
                logger.info(
                    f"Patente detectada con confianza {best_confidence:.2f}: {best_candidate['plate']}"
                )

            if return_full_result:
                return result
            else:
                # Para compatibilidad con código existente, retornar solo string
                return best_candidate["plate"] if not needs_confirm else None

        except Exception as e:
            logger.error(f"Error procesando imagen con EasyOCR: {e}", exc_info=True)
            return (
                None
                if not return_full_result
                else {
                    "plate": None,
                    "confidence": 0.0,
                    "needs_manual_confirm": True,
                    "candidates": [],
                }
            )

    def _preprocess_image(self, img) -> np.ndarray:
        """
        Pre-procesar imagen para mejorar la detección de texto.
        Optimizado para imágenes de celulares modernos (hasta 12MP).

        Args:
            img: Imagen OpenCV (numpy array)

        Returns:
            Imagen procesada
        """
        try:
            # 1. Reescalar si la imagen es muy grande (optimización para celulares 12MP)
            # EasyOCR funciona bien con imágenes de hasta ~2000px, más grande solo ralentiza
            MAX_DIMENSION = 2000  # píxeles
            height, width = img.shape[:2]
            max_dim = max(height, width)

            if max_dim > MAX_DIMENSION:
                # Calcular nuevo tamaño manteniendo aspect ratio
                scale = MAX_DIMENSION / max_dim
                new_width = int(width * scale)
                new_height = int(height * scale)
                img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
                logger.debug(f"Imagen reescalada de {width}x{height} a {new_width}x{new_height}")

            # 2. Convertir a escala de grises (mejor rendimiento que RGB)
            if len(img.shape) == 3:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            else:
                gray = img

            # 3. Aplicar filtro bilateral para reducir ruido manteniendo bordes
            denoised = cv2.bilateralFilter(gray, 5, 50, 50)

            # 4. Aplicar umbral adaptativo para mejorar contraste
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            return thresh
        except Exception as e:
            logger.warning(f"Error en pre-procesamiento, usando imagen original: {e}")
            return img

    def _find_all_plates_in_text(self, text_items: list) -> list:
        """
        Buscar todas las patentes posibles en una lista de textos detectados.

        Args:
            text_items: Lista de dicts con {'text': str, 'confidence': float}

        Returns:
            Lista de candidatos: [{'plate': str, 'confidence': float, 'country': str, 'regex_match': bool}, ...]
        """
        candidates = []

        # Combinar todos los textos para búsqueda global
        combined_text = " ".join([item["text"] for item in text_items])
        combined_clean = (
            re.sub(r"[^\w\s-]", "", combined_text.upper()).replace(" ", "").replace("-", "")
        )

        # Buscar en cada texto individual y en el texto combinado
        search_texts = [
            {
                "text": combined_clean,
                "confidence": max([item["confidence"] for item in text_items], default=0.0),
            }
        ]
        search_texts.extend(
            [
                {
                    "text": re.sub(r"[^\w\s-]", "", item["text"].upper())
                    .replace(" ", "")
                    .replace("-", ""),
                    "confidence": item["confidence"],
                }
                for item in text_items
            ]
        )

        patterns_by_country = {
            "CHILE": [
                (r"^[A-Z]{4}\d{2}$", True),  # Formato nuevo: ABCD12
                (r"^[A-Z]{2}\d{4}$", True),  # Formato antiguo: AB1234
                (r"^[A-Z]{3}\d{4}$", True),  # Alternativo: ABC1234
            ],
            "ARGENTINA": [
                (r"^[A-Z]{3}\d{3}$", True),  # Formato antiguo: ABC123
                (r"^[A-Z]{2}\d{3}[A-Z]{2}$", True),  # Mercosur: AB123CD
            ],
            "BRASIL": [
                (r"^[A-Z]{3}\d[A-Z]\d{2}$", True),  # Mercosur Brasil: ABC1D23
            ],
            "URUGUAY": [
                (r"^[A-Z]{3}\d{4}$", True),  # Formato estándar: ABC1234
            ],
            "USA": [
                (r"^[A-Z]{3}\d{4}$", True),  # Formato común: ABC1234
                (r"^[A-Z]{1,3}\d{1,4}$", True),  # Variaciones
            ],
            "GENERIC": [
                (r"^[A-Z]{2,4}\d{2,4}$", False),  # Patrón genérico (menor prioridad)
                (r"^\d{2,4}[A-Z]{2,4}$", False),  # Invertido
            ],
        }

        countries_to_try = ["CHILE", "ARGENTINA", "BRASIL", "URUGUAY", "USA", "GENERIC"]

        for country in countries_to_try:
            patterns = patterns_by_country.get(country, patterns_by_country["GENERIC"])
            for pattern, is_strict in patterns:
                for search_item in search_texts:
                    text_clean = search_item["text"]

                    # Buscar coincidencias completas
                    match = re.search(pattern, text_clean)
                    if match:
                        plate = self._normalize_plate(match.group())
                        if plate and not any(c["plate"] == plate for c in candidates):
                            candidates.append(
                                {
                                    "plate": plate,
                                    "confidence": search_item["confidence"],
                                    "country": country,
                                    "regex_match": is_strict,
                                    "priority": (
                                        1 if is_strict else 0
                                    ),  # Mayor prioridad si match estricto
                                }
                            )

                    # Buscar coincidencias parciales
                    pattern_partial = pattern.replace("^", "").replace("$", "")
                    matches = re.findall(pattern_partial, text_clean)
                    for match_text in matches:
                        plate = self._normalize_plate(match_text)
                        if plate and not any(c["plate"] == plate for c in candidates):
                            candidates.append(
                                {
                                    "plate": plate,
                                    "confidence": search_item["confidence"],
                                    "country": country,
                                    "regex_match": is_strict,
                                    "priority": 0.5 if is_strict else 0,
                                }
                            )

        return candidates

    def _prioritize_candidates(self, candidates: list) -> list:
        """
        Ordenar candidatos por prioridad: regex_match (país específico) > confianza.

        Args:
            candidates: Lista de candidatos

        Returns:
            Lista ordenada por prioridad (mejor primero)
        """

        def sort_key(candidate):
            # Prioridad 1: regex_match estricto (país específico)
            # Prioridad 2: confianza
            return (-candidate["priority"], -candidate["confidence"])

        return sorted(candidates, key=sort_key)

    def _find_plate_in_text(self, text: str) -> Optional[str]:
        """
        Buscar patente en un texto usando patrones regex específicos por país.

        Args:
            text: Texto completo extraído del OCR

        Returns:
            Patente encontrada o None
        """
        # Limpiar texto: remover espacios, guiones comunes, caracteres especiales
        text_clean = re.sub(r"[^\w\s-]", "", text.upper())
        text_clean = text_clean.replace(" ", "").replace("-", "")

        # Diccionario de patrones por país (orden de prioridad)
        patterns_by_country = {
            "CHILE": [
                r"^[A-Z]{4}\d{2}$",  # Formato nuevo: ABCD12 (4 letras + 2 números)
                r"^[A-Z]{2}\d{4}$",  # Formato antiguo: AB1234 (2 letras + 4 números)
                r"^[A-Z]{3}\d{4}$",  # Alternativo: ABC1234
            ],
            "ARGENTINA": [
                r"^[A-Z]{3}\d{3}$",  # Formato antiguo: ABC123
                r"^[A-Z]{2}\d{3}[A-Z]{2}$",  # Mercosur: AB123CD
            ],
            "BRASIL": [
                r"^[A-Z]{3}\d[A-Z]\d{2}$",  # Mercosur Brasil: ABC1D23
            ],
            "URUGUAY": [
                r"^[A-Z]{3}\d{4}$",  # Formato estándar: ABC1234
            ],
            "USA": [
                r"^[A-Z]{3}\d{4}$",  # Formato común: ABC1234
                r"^[A-Z]{1,3}\d{1,4}$",  # Variaciones
                r"^[A-Z0-9]{1,7}$",  # Genérico (último recurso)
            ],
            "GENERIC": [
                r"^[A-Z]{2,4}\d{2,4}$",  # Patrón genérico
                r"^\d{2,4}[A-Z]{2,4}$",  # Invertido: números + letras
            ],
        }

        # Intentar detectar país desde settings o usar patrones genéricos
        # Obtener país del request si está disponible (se pasa desde las vistas)
        detected_country = getattr(self, "_detected_country", None)
        if not detected_country:
            # Intentar detectar desde empresa en settings
            try:
                from django.contrib.auth.models import AnonymousUser

                # Por ahora usar patrones genéricos y específicos
                countries_to_try = ["CHILE", "ARGENTINA", "BRASIL", "URUGUAY", "USA", "GENERIC"]
            except:
                countries_to_try = ["GENERIC", "CHILE", "USA"]
        else:
            countries_to_try = [detected_country, "GENERIC"]

        # Buscar en cada país según prioridad
        for country in countries_to_try:
            patterns = patterns_by_country.get(country, patterns_by_country["GENERIC"])
            for pattern in patterns:
                # Buscar coincidencias completas
                match = re.search(pattern, text_clean)
                if match:
                    normalized = self._normalize_plate(match.group())
                    if normalized:
                        logger.info(
                            f"Patente encontrada ({country}) con patrón {pattern}: {normalized}"
                        )
                        return normalized

                # También buscar coincidencias parciales (más flexible)
                matches = re.findall(pattern.replace("^", "").replace("$", ""), text_clean)
                for match_text in matches:
                    normalized = self._normalize_plate(match_text)
                    if normalized:
                        logger.info(
                            f"Patente encontrada ({country}) parcial con patrón {pattern}: {normalized}"
                        )
                        return normalized

        # Si no se encontró con patrones estrictos, intentar búsqueda flexible
        flexible_pattern = r"\b[A-Z]{2,6}\d{2,6}\b"
        matches = re.findall(flexible_pattern, text_clean)
        for match_text in matches:
            normalized = self._normalize_plate(match_text)
            if normalized:
                logger.info(f"Patente encontrada con patrón flexible: {normalized}")
                return normalized

        return None

    def _normalize_plate(self, text: str) -> Optional[str]:
        """
        Normalizar texto de patente detectado.

        Args:
            text: Texto crudo del OCR

        Returns:
            Patente normalizada o None si no es válida
        """
        if not text:
            return None

        # Limpiar y normalizar
        text = text.strip().upper()
        # Remover espacios, guiones y caracteres especiales
        text = re.sub(r"[^A-Z0-9]", "", text)

        # Validar formato básico
        # Debe tener al menos 4 caracteres y máximo 8
        # Debe contener al menos una letra y un número
        if len(text) < 4 or len(text) > 8:
            return None

        # Debe contener letras y números
        if not re.search(r"[A-Z]", text) or not re.search(r"[0-9]", text):
            return None

        # Validar que no sea solo números (para evitar falsos positivos)
        if text.isdigit():
            return None

        return text
