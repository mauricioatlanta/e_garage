"""
ImageIndexBuilder — escanea directorios una vez y construye image_index.json.

El índice mapea nombre_de_archivo (case-insensitive) → lista de rutas absolutas.

    {
        "lt043.png":  ["/media/productos/SILENCIADORES/LT043.png"],
        "dw002.jpg":  ["/media/productos/FLEXIBLES/DW002.jpg"],
        "cat001.png": ["/media/catalogo/CAT001.png", "/imagenes/old/CAT001.png"]  ← ambiguo
    }

Una vez construido, MediaResolver lo carga y hace lookups O(1) en lugar de
hacer glob(**) por cada imagen durante la importación.

Uso típico:
    python manage.py build_image_index \\
        --dirs /mnt/datos/media/productos /mnt/datos/imagenes \\
        --output /mnt/datos/image_index.json
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = frozenset(
    {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".bmp", ".tiff", ".tif"}
)


class ImageIndexBuilder:
    """
    Escanea una lista de directorios raíz y construye un índice de imágenes.

    El índice es case-insensitive: 'LT043.PNG', 'lt043.png' y 'Lt043.Png'
    colapsan a la misma clave 'lt043.png'. Si hay múltiples archivos con el
    mismo nombre (case-insensitive) quedan en la lista y MediaResolver los
    reportará como ambiguos.
    """

    def __init__(
        self,
        search_roots: list[str | Path],
        output_path: str | Path,
    ) -> None:
        self._roots = [Path(r) for r in search_roots]
        self._output = Path(output_path)

    def build(self) -> dict[str, list[str]]:
        """
        Escanea todos los roots, construye el índice y lo escribe en output_path.
        Devuelve el índice generado.
        """
        index: dict[str, list[str]] = {}
        total = 0

        for root in self._roots:
            if not root.exists():
                logger.warning("Directorio no encontrado, omitido: %s", root)
                continue
            if not root.is_dir():
                logger.warning("No es un directorio, omitido: %s", root)
                continue
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                if path.suffix.lower() not in IMAGE_EXTENSIONS:
                    continue
                key = path.name.lower()
                index.setdefault(key, []).append(str(path))
                total += 1

        # Orden determinista dentro de cada lista (facilita revisión manual)
        for key in index:
            index[key].sort()

        data = {
            "_meta": {
                "generated_at": datetime.now(tz=timezone.utc).isoformat(),
                "roots": [str(r) for r in self._roots],
                "total_files": total,
                "unique_names": len(index),
                "ambiguous_names": sum(1 for v in index.values() if len(v) > 1),
            },
            "index": index,
        }

        self._output.parent.mkdir(parents=True, exist_ok=True)
        self._output.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        logger.info(
            "image_index.json escrito: %d archivos, %d nombres únicos, %d ambiguos → %s",
            total, len(index),
            data["_meta"]["ambiguous_names"],
            self._output,
        )
        return index

    @staticmethod
    def load(index_path: str | Path) -> dict[str, list[str]]:
        """Carga un índice previamente generado y devuelve solo la sección 'index'."""
        path = Path(index_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        # Soporte para formato plano (legado) y formato envuelto con _meta
        if "index" in data:
            return data["index"]
        return data

    @staticmethod
    def stats(index: dict[str, list[str]]) -> dict:
        total = sum(len(v) for v in index.values())
        ambiguous = sum(1 for v in index.values() if len(v) > 1)
        return {
            "total_files": total,
            "unique_names": len(index),
            "ambiguous_names": ambiguous,
        }
