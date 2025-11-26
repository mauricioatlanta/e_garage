import shutil
from pathlib import Path

BASE_DIR = Path(r"E:\projecto\e_garage")
ARCHIVE_ROOT = BASE_DIR / "templates" / "_archive" / "20251123_vehiculos_cleanup"

# Directorios de vehículos que ya no encajan con la nueva estructura por país
PATTERNS = [
    "templates/cl/en/taller/vehiculos",  # Chile en inglés (no lo usamos)
    "templates/cl/es/taller/vehiculos",  # viejo path de Chile
    "templates/taller/cl/es/vehiculos",  # viejo path de Chile
    "templates/taller/us/en/vehiculos",  # viejo path USA en
    "templates/taller/us/es/vehiculos",  # viejo path USA es
    "templates/taller/vehiculos",  # módulo genérico viejo
    "templates/us/en/taller/vehiculos",  # backup viejo de USA en
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
    print("=== Limpieza módulo VEHICULOS ===")
    print(f"Archivo destino: {ARCHIVE_ROOT}")
    for pattern in PATTERNS:
        move_path(pattern, dry_run=dry_run)


if __name__ == "__main__":
    # 1) Primero probar sin mover nada
    # main(dry_run=True)

    # Cuando estés conforme con la salida, comenta la línea anterior
    # y descomenta esta para ejecutar de verdad:
    main(dry_run=False)
