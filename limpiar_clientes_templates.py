import shutil
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(r"E:\projecto\e_garage")
ARCHIVE_ROOT = BASE_DIR / "templates" / "_archive" / "20251123_clientes_cleanup"

# Rutas de clientes que queremos archivar
PATTERNS = [
    "templates/clientes",  # carpeta vacía
    "templates/taller/clientes",  # carpeta y sus archivos
    "templates/taller/cliente_detail.html",
    "templates/taller/cliente_form.html",
    "templates/taller/cliente_list.html",
    "templates/taller/cl/es/clientes",  # versión antigua Chile
    "templates/taller/us/en/clientes",  # versión antigua USA en
    "templates/taller/us/es/clientes",  # versión antigua USA es
    # opcional: ejemplo
    # "templates/ejemplos/cliente_form_unified.html",
]


def move_path(rel_path: str, dry_run: bool = True):
    src = BASE_DIR / rel_path
    if not src.exists():
        print(f"[SKIP] No existe: {src}")
        return

    # Usamos misma estructura dentro de ARCHIVE_ROOT
    dst = ARCHIVE_ROOT / rel_path

    print(f"{'DRY-RUN' if dry_run else 'MOVE   '} {src} -> {dst}")
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))


def main(dry_run: bool = True):
    print("=== Limpieza módulo CLIENTES ===")
    print(f"Archivo destino: {ARCHIVE_ROOT}")
    for pattern in PATTERNS:
        move_path(pattern, dry_run=dry_run)


if __name__ == "__main__":
    # 1) Primero probar sin mover nada
    # main(dry_run=True)

    # Cuando estés conforme con la salida, comenta la línea anterior
    # y descomenta esto para ejecutar de verdad:
    main(dry_run=False)
