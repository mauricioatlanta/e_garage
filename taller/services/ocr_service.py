import logging
from typing import Iterable, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

try:
    import easyocr  # type: ignore[attr-defined]

    _EASYOCR_IMPORTED = True
except Exception:
    easyocr = None  # type: ignore[assignment]
    _EASYOCR_IMPORTED = False


def _is_ocr_enabled() -> bool:
    """
    Feature flag centralizado para OCR.

    - Por defecto desactivado.
    - Se puede habilitar vía settings.EGARAGE_ENABLE_OCR o env DJANGO_EGARAGE_ENABLE_OCR.
    """
    enabled = getattr(settings, "EGARAGE_ENABLE_OCR", False)
    return bool(enabled)


class OCRService:
    """
    Servicio OCR opcional para eGarage.

    - Solo intenta usar EasyOCR si:
      - El feature flag EGARAGE_ENABLE_OCR está activo, y
      - El paquete easyocr está instalado.
    - Si no, retorna siempre [] sin errores ni warnings ruidosos.
    """

    def __init__(self, languages: Optional[Iterable[str]] = None, gpu: bool = False) -> None:
        self._enabled = _is_ocr_enabled() and _EASYOCR_IMPORTED
        self._gpu = bool(gpu)
        self._languages = list(languages) if languages is not None else ["es", "en"]
        self._reader = None

        if not self._enabled:
            # Mantener silencio en servidores donde OCR no se usa.
            # Solo si el feature flag está ACTIVADO pero falta easyocr, registramos aviso.
            if getattr(settings, "EGARAGE_ENABLE_OCR", False) and not _EASYOCR_IMPORTED:
                logger.warning(
                    "OCR habilitado (EGARAGE_ENABLE_OCR=True) pero easyocr no está instalado. "
                    "Ejecuta: pip install easyocr opencv-python-headless"
                )
            return

        try:
            self._reader = easyocr.Reader(self._languages, gpu=self._gpu)  # type: ignore[call-arg]
        except Exception as exc:
            logger.warning("OCR: inicialización de EasyOCR falló: %s", exc, exc_info=True)
            self._reader = None

    def is_available(self) -> bool:
        """
        Indica si OCR está realmente disponible (flag + paquete + reader OK).
        """
        return bool(self._reader)

    def read_text(self, image_path: str) -> List[str]:
        """
        Lee texto desde una imagen.

        - Si OCR no está disponible, retorna [] silenciosamente.
        - Si ocurre un error al leer, también retorna [] pero registra el error.
        """
        if not self._reader:
            return []

        try:
            results = self._reader.readtext(image_path)
            # EasyOCR retorna típicamente [ [bbox, text, conf], ... ] o [text, ...]
            out: List[str] = []
            for item in results or []:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    out.append(str(item[1]))
                else:
                    out.append(str(item))
            return out
        except Exception as exc:
            logger.error("OCR: error leyendo texto desde %s: %s", image_path, exc, exc_info=True)
            return []
