"""
Script para mover archivos restantes de taller/cl/es y taller/us a cl/es y us.
"""

import shutil
from pathlib import Path

BASE_DIR = Path(r"E:\projecto\e_garage")


def move_file(src: Path, dst: Path, dry_run: bool = True):
    """Mueve un archivo, creando directorios si es necesario."""
    if not src.exists():
        print(f"[WARN] No existe: {src}")
        return False

    if dst.exists():
        print(f"[WARN] DESTINO YA EXISTE, no muevo: {src} -> {dst}")
        return False

    print(
        f"{'DRY-RUN ' if dry_run else 'MOVE    '} {src.relative_to(BASE_DIR)} -> {dst.relative_to(BASE_DIR)}"
    )
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
    return True


def mover_archivos_restantes(dry_run: bool = True):
    """Mueve archivos restantes de taller/cl/es y taller/us a cl/es y us."""
    print("=" * 80)
    print("MOVIENDO ARCHIVOS RESTANTES POR PAÍS")
    print("=" * 80)
    print(f"Modo: {'DRY-RUN (simulación)' if dry_run else 'EJECUCIÓN REAL'}")
    print("=" * 80)

    # Mover de taller/cl/es/* a cl/es/*
    for path in BASE_DIR.rglob("templates/taller/cl/es/**/*.html"):
        if path.is_dir():
            continue
        if "_archive" in str(path) or "revision" in str(path) or "backup" in str(path):
            continue

        rel = path.relative_to(BASE_DIR)
        new_rel_str = str(rel).replace("templates/taller/cl/es/", "templates/cl/es/")
        new_rel = Path(new_rel_str)
        dst = BASE_DIR / new_rel

        # Evitar mover si el destino es el mismo que el origen
        if str(rel) == new_rel_str:
            continue

        # No mover archivos base (base.html, etc.) que son específicos de taller/
        if path.name in ["base.html"]:
            print(f"[SKIP] Archivo base, mantener en taller/: {path.name}")
            continue

        move_file(path, dst, dry_run)

    # Mover de taller/us/en/* a us/en/*
    for path in BASE_DIR.rglob("templates/taller/us/en/**/*.html"):
        if path.is_dir():
            continue
        if "_archive" in str(path) or "revision" in str(path) or "backup" in str(path):
            continue

        rel = path.relative_to(BASE_DIR)
        new_rel_str = str(rel).replace("templates/taller/us/en/", "templates/us/en/")
        new_rel = Path(new_rel_str)
        dst = BASE_DIR / new_rel

        # Evitar mover si el destino es el mismo que el origen
        if str(rel) == new_rel_str:
            continue

        # No mover archivos base (base.html, etc.) que son específicos de taller/
        if path.name in ["base.html"]:
            print(f"[SKIP] Archivo base, mantener en taller/: {path.name}")
            continue

        move_file(path, dst, dry_run)

    # Mover de taller/us/es/* a us/es/*
    for path in BASE_DIR.rglob("templates/taller/us/es/**/*.html"):
        if path.is_dir():
            continue
        if "_archive" in str(path) or "revision" in str(path) or "backup" in str(path):
            continue

        rel = path.relative_to(BASE_DIR)
        new_rel_str = str(rel).replace("templates/taller/us/es/", "templates/us/es/")
        new_rel = Path(new_rel_str)
        dst = BASE_DIR / new_rel

        # Evitar mover si el destino es el mismo que el origen
        if str(rel) == new_rel_str:
            continue

        move_file(path, dst, dry_run)

    print("\n" + "=" * 80)
    print("MOVIMIENTO COMPLETADO")
    print("=" * 80)


if __name__ == "__main__":
    # Ejecutar en modo real
    mover_archivos_restantes(dry_run=False)
