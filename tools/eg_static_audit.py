#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
eg_static_audit.py

Audita un proyecto Django para encontrar archivos "estáticos" (css, js, imágenes, fuentes, videos)
que estén FUERA de la carpeta /static, sugiere un destino correcto dentro de /static,
detecta duplicados por hash, y opcionalmente los mueve de forma segura.

Uso (Windows PowerShell o CMD):
  py eg_static_audit.py --root "E:\\projecto\\e_garage" --static-root "E:\\projecto\\e_garage\\static" --report "E:\\projecto\\e_garage\tools\reports\\static_audit"
  py eg_static_audit.py --root "E:\\projecto\\e_garage" --static-root "E:\\projecto\\e_garage\\static" --move

Por defecto es dry-run (no mueve nada). Use --move para ejecutar.
"""

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# --- Configuración de extensiones y subcarpetas de destino bajo /static ---
EXT_MAP: Dict[str, str] = {
    # CSS/JS
    ".css": "css",
    ".js": "js",
    ".mjs": "js",
    ".ts": "js",  # si se sube TS sin compilar
    # Imágenes
    ".png": "images",
    ".jpg": "images",
    ".jpeg": "images",
    ".gif": "images",
    ".svg": "images",
    ".webp": "images",
    ".ico": "images",
    # Fuentes
    ".ttf": "fonts",
    ".otf": "fonts",
    ".woff": "fonts",
    ".woff2": "fonts",
    ".eot": "fonts",
    # Videos / Media pesada
    ".mp4": "videos",
    ".webm": "videos",
    ".mov": "videos",
    ".avi": "videos",
    # Audio
    ".mp3": "audio",
    ".ogg": "audio",
    ".wav": "audio",
}

# --- Carpetas a ignorar durante el recorrido ---
DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "venv",
    ".venv",
    "env",
    ".env",
    "migrations",
    "media",
    "staticfiles",
    "collectstatic",
    ".idea",
    ".vscode",
    ".DS_Store",
    "tools\\reports",
    "tools/reports",
}

# --- Patrones de archivo a ignorar (copias/temporal) para reportes severos ---
IGNORE_FILE_PATTERNS = [
    r"^~\$",
]

TEMPLATE_EXTS = {".html", ".jinja", ".jinja2", ".htm"}


def norm(p: Path) -> str:
    return str(p).replace("/", os.sep).replace("\\", os.sep)


def is_hidden(p: Path) -> bool:
    name = p.name
    return name.startswith(".") and name not in {".env", ".env.example"}


def sha256_of_file(path: Path, blocksize: int = 65536) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(blocksize), b""):
            h.update(chunk)
    return h.hexdigest()


def should_scan_dir(d: Path, excludes: set) -> bool:
    name = d.name
    if name in excludes:
        return False
    # Evitar directorios ocultos
    if is_hidden(d):
        return False
    return True


def collect_static_like_files(
    root: Path, static_root: Path, excludes: set
) -> Tuple[List[Path], List[Path]]:
    static_inside: List[Path] = []
    static_outside: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Filtrar subdirectorios
        dirnames[:] = [
            d for d in dirnames if should_scan_dir(Path(dirpath) / d, excludes)
        ]
        for fname in filenames:
            p = Path(dirpath) / fname
            ext = p.suffix.lower()
            if ext in EXT_MAP:
                if static_root in p.parents or p == static_root:
                    static_inside.append(p)
                else:
                    static_outside.append(p)
    return static_inside, static_outside


def find_duplicates_by_hash(paths: List[Path]) -> Dict[str, List[Path]]:
    dup_map: Dict[str, List[Path]] = {}
    for p in paths:
        try:
            h = sha256_of_file(p)
        except Exception:
            # Si no se puede leer, continuar
            continue
        dup_map.setdefault(h, []).append(p)
    # Quedarse con solo los que tienen más de 1
    return {k: v for k, v in dup_map.items() if len(v) > 1}


def suggest_destination(static_root: Path, src: Path) -> Path:
    """Sugiere destino bajo /static con subcarpeta por extensión y nombre seguro."""
    sub = EXT_MAP.get(src.suffix.lower(), "misc")
    target_dir = static_root / sub
    target_dir.mkdir(parents=True, exist_ok=True)
    # mantén el nombre base; si colisiona, agrega hash corto
    base = src.name
    dest = target_dir / base
    if dest.exists():
        try:
            h = sha256_of_file(src)[:8]
        except Exception:
            h = "conflict"
        stem, ext = os.path.splitext(base)
        dest = target_dir / f"{stem}.{h}{ext}"
    return dest


def scan_template_references(root: Path) -> Dict[str, int]:
    """
    Cuenta referencias simples a recursos estáticos en templates.
    Busca patrones {"static '...'"}, href/src comunes y nombres de archivo.
    No es perfecto, pero ayuda a priorizar qué parece usado.
    """
    REF_COUNTER: Dict[str, int] = {}
    static_tag_re = re.compile(r"\{%\s*static\s+['\"]([^'\"]+)['\"]\s*%\}")
    href_src_re = re.compile(r"""(?:href|src)\s*=\s*['"]([^'"]+)['"]""")
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d
            for d in dirnames
            if should_scan_dir(Path(dirpath) / d, DEFAULT_EXCLUDE_DIRS)
        ]
        for fname in filenames:
            p = Path(dirpath) / fname
            if p.suffix.lower() in TEMPLATE_EXTS:
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                for m in static_tag_re.finditer(text):
                    REF_COUNTER[m.group(1)] = REF_COUNTER.get(m.group(1), 0) + 1
                for m in href_src_re.finditer(text):
                    REF_COUNTER[m.group(1)] = REF_COUNTER.get(m.group(1), 0) + 1
    return REF_COUNTER


def main():
    parser = argparse.ArgumentParser(
        description="Audita y migra estáticos hacia /static"
    )
    parser.add_argument(
        "--root",
        required=True,
        help="Ruta raíz del proyecto (ej. E:\\projecto\\e_garage)",
    )
    parser.add_argument(
        "--static-root", required=True, help="Ruta de la carpeta /static del proyecto"
    )
    parser.add_argument(
        "--report",
        default="",
        help="Prefijo de salida para reportes (CSV y JSON). Si no se indica, usa ./static_audit_report_YYYYmmdd_HHMMSS",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Mover archivos sugeridos (por defecto es dry-run)",
    )
    parser.add_argument(
        "--include-ts",
        action="store_true",
        help="Incluir archivos .ts (TypeScript) en el plan",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    static_root = Path(args.static_root).resolve()

    if not root.exists():
        raise SystemExit(f"[ERROR] --root no existe: {root}")
    if not static_root.exists():
        print(f"[INFO] Creando static-root: {static_root}")
        static_root.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_prefix = (
        Path(args.report) if args.report else Path.cwd() / f"static_audit_report_{ts}"
    )
    report_csv = Path(str(report_prefix) + ".csv")
    report_json = Path(str(report_prefix) + ".json")

    excludes = set(DEFAULT_EXCLUDE_DIRS)

    # Opcional: excluir .ts si no se especifica
    if not args.include_ts:
        if ".ts" in EXT_MAP:
            del EXT_MAP[".ts"]

    print(f"[START] Escaneando proyecto: {root}")
    print(f"[INFO] Carpeta estáticos: {static_root}")

    inside, outside = collect_static_like_files(root, static_root, excludes)

    print(f"[INFO] Estáticos dentro de /static: {len(inside)}")
    print(f"[INFO] Estáticos fuera  de /static: {len(outside)}")

    # Duplicados por hash (entre todos)
    print("[INFO] Buscando duplicados por hash (esto puede tardar un poco)...")
    dups_all = find_duplicates_by_hash(inside + outside)

    # Conteo de referencias en templates (para priorizar)
    print("[INFO] Escaneando referencias en templates...")
    ref_counter = scan_template_references(root)

    plan_rows: List[Dict] = []
    moved_rows: List[Dict] = []

    for src in outside:
        ext = src.suffix.lower()
        size = src.stat().st_size
        sha = ""
        try:
            sha = sha256_of_file(src)
        except Exception:
            pass

        # Sugerir destino
        dest = suggest_destination(static_root, src)
        rel_dest = dest.relative_to(static_root) if dest.is_absolute() else dest

        # Heurísticas de acción sugerida
        action = "move"
        reason = "static-like outside /static"

        # Si es copia temporal/backup por nombre
        name_lower = src.name.lower()
        if any(re.search(pat, src.name) for pat in IGNORE_FILE_PATTERNS) or any(
            tok in name_lower
            for tok in ["backup", "copy", "old", "temp", "tmp", "(1)", "(2)"]
        ):
            # Si pesa poco y parece backup, sugerir borrar
            if size < 1024 * 1024 * 3:  # < 3MB
                action = "delete"
                reason = "probable backup/copia temporal"

        # Si hay un duplicado exacto ya dentro de /static, sugerir borrar este
        if sha and sha in dups_all:
            # si alguno de los duplicados está en static, eliminar la versión fuera
            if any(static_root in p.parents for p in dups_all[sha]):
                action = "delete"
                reason = "duplicado: ya existe dentro de /static"

        # Si parece una librería dentro de /templates, forzar move
        if "templates" in norm(src).lower() and ext in {".css", ".js"}:
            action = "move"
            reason = "recurso enlazado desde templates"

        # Conteo de referencias por nombre de archivo (heurística básica)
        ref_hits = 0
        for k, v in ref_counter.items():
            if src.name in k:
                ref_hits += v

        plan_rows.append(
            {
                "src": norm(src),
                "size_kb": round(size / 1024, 2),
                "sha256": sha[:16],
                "suggested_action": action,
                "reason": reason,
                "suggested_dest_under_static": norm(rel_dest),
                "ref_hits_in_templates": ref_hits,
            }
        )

    # Guardar reportes
    report_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(report_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=(
                list(plan_rows[0].keys())
                if plan_rows
                else [
                    "src",
                    "size_kb",
                    "sha256",
                    "suggested_action",
                    "reason",
                    "suggested_dest_under_static",
                    "ref_hits_in_templates",
                ]
            ),
        )
        w.writeheader()
        for row in plan_rows:
            w.writerow(row)

    with open(report_json, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": ts,
                "root": norm(root),
                "static_root": norm(static_root),
                "totals": {
                    "inside_static": len(inside),
                    "outside_static": len(outside),
                    "duplicates_groups": len(dups_all),
                },
                "plan": plan_rows,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("[DONE] Reportes generados:")
    print(f" - CSV : {report_csv}")
    print(f" - JSON: {report_json}")

    # Ejecutar movimiento si se pidió
    if args.move:
        print("[EXEC] Movimiento habilitado (--move).")
        for row in plan_rows:
            if row["suggested_action"] == "move":
                src = Path(row["src"])
                dest = static_root / row["suggested_dest_under_static"]
                dest.parent.mkdir(parents=True, exist_ok=True)
                try:
                    dest_exists = dest.exists()
                    shutil.move(str(src), str(dest))
                    moved_rows.append(
                        {
                            "src": row["src"],
                            "dest": norm(dest),
                            "overwrote": dest_exists,
                        }
                    )
                except Exception as e:
                    print(f"[ERROR] No se pudo mover: {src} -> {dest} :: {e}")

        # Guardar registro de movimientos
        moves_log = Path(str(report_prefix) + "_moves.json")
        with open(moves_log, "w", encoding="utf-8") as f:
            json.dump(moved_rows, f, indent=2, ensure_ascii=False)
        print(f"[DONE] Movimientos registrados en: {moves_log}")


if __name__ == "__main__":
    main()
