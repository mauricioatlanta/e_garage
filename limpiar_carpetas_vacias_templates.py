from pathlib import Path

BASE_DIR = Path(r"E:\projecto\e_garage")
TEMPLATES_DIR = BASE_DIR / "templates"
ARCHIVE_NAME = "_archive"


def listar_carpetas_vacias(dry_run: bool = True):
    if not TEMPLATES_DIR.exists():
        print(f"[ERROR] No existe: {TEMPLATES_DIR}")
        return

    # Listar todas las carpetas dentro de templates
    dirs = [p for p in TEMPLATES_DIR.rglob("*") if p.is_dir()]

    # Ordenar de más profundo a más superficial (para ir borrando de abajo hacia arriba)
    dirs_sorted = sorted(dirs, key=lambda p: len(p.parts), reverse=True)

    print("=== Buscando carpetas vacías en templates/ ===")
    for d in dirs_sorted:
        # Saltar cualquier cosa dentro de _archive
        if ARCHIVE_NAME in d.parts:
            continue

        try:
            # ¿Tiene algo adentro?
            if any(d.iterdir()):
                continue
        except FileNotFoundError:
            # Si ya fue movida/borrada por otro proceso
            continue

        # Si llegamos aquí, está vacía
        print(f"{'DRY-RUN' if dry_run else 'BORRAR '} carpeta vacía: {d}")
        if not dry_run:
            d.rmdir()


if __name__ == "__main__":
    # 1) Primero solo mostrar qué borraría
    # listar_carpetas_vacias(dry_run=True)

    # Cuando estés conforme, comenta la línea de arriba y descomenta esta:
    listar_carpetas_vacias(dry_run=False)
