# taller/utils/ocr.py
from __future__ import annotations

import re
from typing import List, Dict, Any

# -------------------------
# Patente / Plate helpers
# -------------------------

_PLATE_CLEAN_RE = re.compile(r"[^A-Z0-9]")
_CHILE_PATTERNS = [
    re.compile(r"^[A-Z]{4}\d{2}$"),  # ABCD12 (nuevo)
    re.compile(r"^[A-Z]{2}\d{4}$"),  # AB1234 (antiguo)
]


def normalizar_patente(value: str) -> str:
    """
    Normaliza patente:
    - upper
    - elimina espacios, guiones y símbolos
    """
    if not value:
        return ""
    v = value.strip().upper()
    v = _PLATE_CLEAN_RE.sub("", v)
    return v


def es_patente_cl(value: str) -> bool:
    """
    Valida si la patente parece chilena (patrón clásico o nuevo).
    """
    v = normalizar_patente(value)
    return any(p.match(v) for p in _CHILE_PATTERNS)


def filtrar_candidatos_patente(texts: List[str]) -> List[Dict[str, Any]]:
    """
    Recibe lista de strings y devuelve candidatos normalizados,
    priorizando formatos tipo patente.
    """
    out = []
    seen = set()
    for t in texts or []:
        n = normalizar_patente(t)
        if not n or n in seen:
            continue
        seen.add(n)
        # Heurística simple: largo razonable
        if len(n) < 5 or len(n) > 8:
            continue
        score = 0.5
        if es_patente_cl(n):
            score = 0.9
        out.append({"text": n, "score": score})
    # ordenar: primero mejores score, luego más cortos
    out.sort(key=lambda x: (-x["score"], len(x["text"])))
    return out


# -------------------------
# API compatibility: extraer_candidatos_* (usado por ops/api.py)
# -------------------------

_REPUESTO_PATTERN = re.compile(r"[A-Z0-9\-]{4,}")


def extraer_candidatos_patente(textos_ocr: List, top: int = 5) -> List[Dict[str, Any]]:
    """
    De una lista de textos crudos de OCR (strings o tuplas easyocr), normaliza y filtra por patente.
    Retorna lista de {"text": "ABCD12", "score": 0.82} ordenada por score.
    """
    raw_strings: List[str] = []
    for item in textos_ocr or []:
        if isinstance(item, (list, tuple)):
            text = item[1] if len(item) > 1 else str(item)
        else:
            text = str(item)
        raw_strings.append(text)
    return filtrar_candidatos_patente(raw_strings)[:top]


def extraer_candidatos_repuesto(textos_ocr: List, top: int = 10) -> List[str]:
    """
    Filtra textos que parecen códigos de repuesto [A-Z0-9-]{4,}.
    Acepta lista de strings o tuplas (bbox, text, conf). Retorna lista de strings únicos.
    """
    seen = set()
    result: List[str] = []
    for item in textos_ocr or []:
        if isinstance(item, (list, tuple)):
            text = item[1] if len(item) > 1 else str(item)
        else:
            text = str(item)
        for part in re.split(r"[\s,;]+", text):
            part = part.upper().strip()
            if len(part) >= 4 and _REPUESTO_PATTERN.match(part) and part not in seen:
                seen.add(part)
                result.append(part)
                if len(result) >= top:
                    return result
    return result


# -------------------------
# OCR availability
# -------------------------


def is_ocr_available() -> bool:
    try:
        import easyocr  # noqa: F401

        return True
    except Exception:
        return False


def ocr_read_text(image_path: str, langs: List[str] | None = None) -> List[str]:
    """
    OCR básico. Si no hay easyocr, retorna [] sin romper.
    Retorna lista de strings (detail=0).
    """
    langs = langs or ["es", "en"]
    try:
        import easyocr

        reader = easyocr.Reader(langs, gpu=False)
        results = reader.readtext(image_path, detail=0)
        # results suele ser list[str]
        return [str(x) for x in results] if results else []
    except Exception:
        return []
