import shutil
from pathlib import Path

BASE_DIR = Path(r"E:\projecto\e_garage")
ARCHIVE_ROOT = BASE_DIR / "templates" / "_archive" / "20251123_servicios_cleanup"

# Rutas de servicios/otros_servicios que ya no encajan con la nueva estructura
PATTERNS = [
    # Carpetas vacías o legacy
    "templates/servicios",
    "templates/taller/otros_servicios",
    "templates/taller/us/en/servicios",
    "templates/taller/us/es/servicios",
    # Templates antiguos / duplicados respecto a COMMON
    "templates/taller/servicios.html",
    "templates/taller/servicios/servicios_menu.html",
    "templates/taller/servicios/otros_servicios_menu.html",
    "templates/taller/servicios/crear_otro_servicio.html",
    "templates/taller/otros_servicios_list.html",
    "templates/taller/categorias_servicios.html",
]


def move_path(rel_path: str, dry_run: bool = True):
    src = BASE_DIR / rel_path
    if not src.exists():
        print(f"[SKIP] No existe: {src}")
        return

    dst = ARCHIVE_ROOT / rel_path

    print(f"{'DRY-RUN' if dry_run else 'MOVE   '} {src} -> {dst}")
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))


def main(dry_run: bool = True):
    print("=== Limpieza módulo SERVICIOS / OTROS_SERVICIOS ===")
    print(f"Archivo destino: {ARCHIVE_ROOT}")
    for pattern in PATTERNS:
        move_path(pattern, dry_run=dry_run)


if __name__ == "__main__":
    # 1) Primero probar sin mover nada
    # main(dry_run=True)

    # Cuando estés conforme con la salida, comenta la línea anterior
    # y descomenta esta para ejecutar de verdad:
    main(dry_run=False)
