import shutil
from pathlib import Path

BASE_DIR = Path(r"E:\projecto\e_garage")
ARCHIVE_ROOT = BASE_DIR / "templates" / "_archive" / "20251123_documentos_cleanup"

# Rutas de DOCUMENTOS que ya no encajan con la nueva estructura (common + por país)
PATTERNS = [
    # Carpetas vacías / legacy fuera de taller
    "templates/documentos",
    "templates/pdf",
    # Rutas viejas por país dentro de taller
    "templates/taller/cl/es/documentos",
    "templates/taller/us/en/documentos",
    "templates/taller/us/es/documentos",
    # Árbol genérico viejo de documentos
    "templates/taller/documentos",
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
    print("=== Limpieza módulo DOCUMENTOS ===")
    print(f"Archivo destino: {ARCHIVE_ROOT}")
    for pattern in PATTERNS:
        move_path(pattern, dry_run=dry_run)


if __name__ == "__main__":
    # 1) Primero probar sin mover nada
    # main(dry_run=True)

    # Cuando estés conforme con la salida, comenta la línea anterior
    # y descomenta esta para ejecutar de verdad:
    main(dry_run=False)
