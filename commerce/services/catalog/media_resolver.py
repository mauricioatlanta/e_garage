"""
MediaResolver — resuelve paths de imágenes almacenados en la BD hacia archivos físicos.

Casos:
    found     → exactamente 1 match; devuelve Path.
    ambiguous → más de 1 match con el mismo nombre de archivo; devuelve el primero
                (orden lexicográfico) y registra los candidatos para revisión manual.
    missing   → ningún match; devuelve None y registra el path para revisión manual.

Al finalizar la importación, llamar a write_review_if_needed() para generar
manual_review.json únicamente cuando hay casos ambiguos o faltantes.

Modo rápido (con índice):
    Pasar index_path al constructor.  El índice se construye una vez con
    ImageIndexBuilder y reside en disco.  Lookups O(1) por nombre de archivo.

Modo lento (sin índice):
    Glob recursivo en search_dirs por cada resolución.  Igual que antes.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class _AmbiguousRecord:
    db_path: str
    candidates: list[str]


class MediaResolver:
    """
    Resuelve un path almacenado en la BD (p.ej. "products/2026/02/LT043.png")
    hacia el archivo físico en disco.

    Con index_path:
        Carga image_index.json generado por ImageIndexBuilder.
        Lookup O(1) case-insensitive por nombre de archivo.

    Sin index_path (comportamiento original):
        Búsqueda glob recursiva en search_dirs, luego fallback a ruta completa.

    Cuando hay múltiples candidatos (ambiguos), usa el primero en orden
    lexicográfico y registra todos los candidatos para revisión manual.
    """

    def __init__(
        self,
        media_root: str | Path,
        search_dirs: tuple[str, ...] = ("productos",),
        *,
        index_path: str | Path | None = None,
    ) -> None:
        self._media_root = Path(media_root)
        self._search_dirs = search_dirs
        self._missing: list[str] = []
        self._ambiguous: list[_AmbiguousRecord] = []
        self._index: dict[str, list[str]] | None = None

        if index_path is not None:
            idx = Path(index_path)
            if idx.exists():
                from commerce.services.catalog.image_index import ImageIndexBuilder
                self._index = ImageIndexBuilder.load(idx)
                logger.info(
                    "MediaResolver: índice cargado desde %s (%d nombres)",
                    idx, len(self._index),
                )
            else:
                logger.warning(
                    "MediaResolver: index_path especificado pero no encontrado: %s "
                    "— se usará glob como fallback.", idx
                )

    # ── Resolución ────────────────────────────────────────────────

    def resolve(self, db_path: str) -> Path | None:
        """
        Devuelve el archivo físico que mejor coincide con db_path, o None.

        Efectos colaterales:
          - Si no hay candidatos → agrega a _missing.
          - Si hay más de un candidato → agrega a _ambiguous y devuelve el primero.
        """
        filename = Path(db_path).name
        if not filename:
            self._missing.append(db_path)
            return None

        if self._index is not None:
            candidates = self._resolve_from_index(filename)
        else:
            candidates = self._resolve_by_glob(filename, db_path)

        if not candidates:
            self._missing.append(db_path)
            logger.warning("Imagen no encontrada en disco: %s", db_path)
            return None

        candidates.sort()

        if len(candidates) > 1:
            self._ambiguous.append(
                _AmbiguousRecord(
                    db_path=db_path,
                    candidates=[str(p) for p in candidates],
                )
            )
            logger.warning(
                "Imagen ambigua (%d candidatos), usando el primero: %s",
                len(candidates),
                candidates[0],
            )

        return candidates[0]

    def _resolve_from_index(self, filename: str) -> list[Path]:
        key = filename.lower()
        paths = self._index.get(key, [])
        return [Path(p) for p in paths]

    def _resolve_by_glob(self, filename: str, db_path: str) -> list[Path]:
        candidates: list[Path] = []

        for search_dir in self._search_dirs:
            target = self._media_root / search_dir
            if target.is_dir():
                candidates.extend(target.glob(f"**/{filename}"))

        # Fallback: ruta relativa completa bajo media_root
        if not candidates:
            full = self._media_root / db_path
            if full.exists():
                candidates.append(full)

        return candidates

    # ── Estado ────────────────────────────────────────────────────

    @property
    def has_issues(self) -> bool:
        return bool(self._missing or self._ambiguous)

    @property
    def missing_count(self) -> int:
        return len(self._missing)

    @property
    def ambiguous_count(self) -> int:
        return len(self._ambiguous)

    @property
    def missing(self) -> list[str]:
        return list(self._missing)

    @property
    def ambiguous(self) -> list[dict]:
        return [{"db_path": r.db_path, "candidates": r.candidates} for r in self._ambiguous]

    # ── Revisión manual ───────────────────────────────────────────

    def get_review_data(self, empresa_id: int | None = None) -> dict:
        return {
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "empresa_id": empresa_id,
            "summary": {
                "missing": self.missing_count,
                "ambiguous": self.ambiguous_count,
            },
            "missing": list(self._missing),
            "ambiguous": [
                {"db_path": r.db_path, "candidates": r.candidates}
                for r in self._ambiguous
            ],
        }

    def write_review_if_needed(
        self,
        output_path: str | Path,
        empresa_id: int | None = None,
    ) -> bool:
        """
        Escribe manual_review.json si hay imágenes ambiguas o faltantes.
        Devuelve True si el archivo fue escrito.
        """
        if not self.has_issues:
            return False

        output_path = Path(output_path)
        data = self.get_review_data(empresa_id)
        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info("manual_review.json escrito en: %s", output_path)
        return True
