#!/usr/bin/env python3
"""
Fase 1 — Inventario de duplicados en templates/

- Busca solo en templates/
- Solo archivos .html
- Duplicados por hash (contenido idéntico)
- Repetición por nombre (mismo filename en rutas distintas)
- Exporta: duplicates_by_hash.json, duplicates_by_name.json, top_duplicates.md
"""

import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path

# Raíz del repo (donde está templates/)
REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / "templates"
REPORTS_DIR = REPO_ROOT / "reports" / "templates_audit"

# backup/ no está dentro de templates/; por si acaso, saltamos cualquier ruta que lo contenga
SKIP_PATHS = ("backups",)


def norm(path: Path) -> str:
    """Ruta relativa a templates/ para consistencia."""
    rel = path.relative_to(TEMPLATES_DIR)
    return str(rel).replace("\\", "/")


def should_skip(p: Path) -> bool:
    for part in p.parts:
        if part in SKIP_PATHS:
            return True
    return False


def collect_html_files():
    """Recolecta todos los .html bajo templates/ (relativos a REPO_ROOT)."""
    files = []
    for path in TEMPLATES_DIR.rglob("*.html"):
        rel = path.relative_to(REPO_ROOT)
        if should_skip(rel):
            continue
        files.append(path)
    return files


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    files = collect_html_files()
    print(f"[*] Encontrados {len(files)} archivos .html en templates/")

    # --- Por hash (contenido idéntico) ---
    by_hash = defaultdict(list)
    for p in files:
        try:
            data = p.read_bytes()
        except OSError:
            continue
        h = hashlib.sha256(data).hexdigest()
        by_hash[h].append(norm(p))

    # Solo grupos con 2+ archivos
    dup_hash = {h: paths for h, paths in by_hash.items() if len(paths) > 1}
    path_hash = REPORTS_DIR / "duplicates_by_hash.json"
    with open(path_hash, "w", encoding="utf-8") as f:
        json.dump(dup_hash, f, ensure_ascii=False, indent=2)
    print(f"[*] duplicates_by_hash: {len(dup_hash)} grupos -> {path_hash}")

    # --- Por nombre (mismo filename en rutas distintas) ---
    by_name = defaultdict(list)
    for p in files:
        by_name[p.name].append(norm(p))

    dup_name = {name: paths for name, paths in by_name.items() if len(paths) > 1}
    path_name = REPORTS_DIR / "duplicates_by_name.json"
    with open(path_name, "w", encoding="utf-8") as f:
        json.dump(dup_name, f, ensure_ascii=False, indent=2)
    print(f"[*] duplicates_by_name: {len(dup_name)} nombres -> {path_name}")

    # --- top_duplicates.md ---
    lines = [
        "# Auditoría de duplicados — templates/",
        "",
        f"Total .html escaneados: {len(files)}",
        f"Grupos por hash (contenido idéntico): {len(dup_hash)}",
        f"Nombres repetidos (mismo filename): {len(dup_name)}",
        "",
        "---",
        "",
        "## Top duplicados por hash (grupos más grandes primero)",
        "",
    ]

    # Ordenar por tamaño de grupo desc
    sorted_hash = sorted(dup_hash.items(), key=lambda x: -len(x[1]))
    for i, (h, paths) in enumerate(sorted_hash[:50], 1):
        lines.append(f"### #{i} — {len(paths)} copias (hash: {h[:12]}…)")
        lines.append("")
        for r in sorted(paths):
            lines.append(f"- `{r}`")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Top nombres repetidos (mismo filename, más rutas primero)",
            "",
        ]
    )
    sorted_name = sorted(dup_name.items(), key=lambda x: -len(x[1]))
    for i, (name, paths) in enumerate(sorted_name[:50], 1):
        lines.append(f"### #{i} — `{name}` ({len(paths)} rutas)")
        lines.append("")
        for r in sorted(paths):
            lines.append(f"- `{r}`")
        lines.append("")

    # Nota: templates/copy/
    copy_roots = [p for p in files if norm(p).startswith("copy/")]
    if copy_roots:
        in_copy_hash = sum(
            1 for paths in dup_hash.values() if any(r.startswith("copy/") for r in paths)
        )
        lines.append("---")
        lines.append("")
        lines.append("## Nota: templates/copy/")
        lines.append(
            f"Archivos .html bajo copy/: {len(copy_roots)}. Grupos por hash que involucran copy/: {in_copy_hash}."
        )

    path_md = REPORTS_DIR / "top_duplicates.md"
    path_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"[*] top_duplicates.md -> {path_md}")
    print("[*] Hecho.")


if __name__ == "__main__":
    main()
