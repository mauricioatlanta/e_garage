import shutil
from pathlib import Path
import re

BASE_DIR = Path(r"E:\projecto\e_garage")
ARCHIVE_ROOT = BASE_DIR / "templates" / "_archive" / "20251123_estructura_final_cleanup"

# Movimientos de archivos (no carpetas completas)
MOVES = [
    # Logins país-específicos
    {
        "src": "templates/taller/cl/es/account/login.html",
        "dst": "templates/cl/es/account/login.html",
        "type": "move",
    },
    {
        "src": "templates/taller/us/en/account/login.html",
        "dst": "templates/us/en/account/login.html",
        "type": "move",
    },
    # Dashboards país-específicos
    {
        "src": "templates/taller/cl/es/dashboard/centro_operaciones.html",
        "dst": "templates/cl/es/dashboard/centro_operaciones.html",
        "type": "move",
    },
    {
        "src": "templates/taller/us/en/dashboard/centro_operaciones_espacial.html",
        "dst": "templates/us/en/dashboard/centro_operaciones_espacial.html",
        "type": "move",
    },
    # Dashboard suelto en us/
    {
        "src": "templates/us/centro_operaciones_espacial.html",
        "dst": "templates/us/en/dashboard/centro_operaciones_espacial_alt.html",
        "type": "move",
    },
    # Dashboard Chile suelto
    {
        "src": "templates/cl/dashboard_chile.html",
        "dst": "templates/cl/es/dashboard/dashboard_chile.html",
        "type": "move",
    },
]

# Carpetas completas a archivar
ARCHIVE_PATTERNS = [
    "templates/common",  # Carpeta completa legacy
]

# Archivos legacy de repuestos a archivar
REPUESTO_LEGACY = [
    "templates/taller/repuesto_detail.html",
    "templates/taller/repuesto_form.html",
    "templates/taller/repuesto_form_backup.html",
    "templates/taller/repuesto_form_clean.html",
    "templates/taller/repuesto_form_final.html",
    "templates/taller/repuesto_form_limpio.html",
    "templates/taller/repuesto_form_new.html",
    "templates/taller/repuesto_form_new_clean.html",
    "templates/taller/repuesto_form_nuevo.html",
    "templates/taller/repuesto_list.html",
]

# Archivos a actualizar en código Python
CODE_UPDATES = [
    {
        "file": "taller/repuestos/views_cbv.py",
        "old": "taller/repuesto_form.html",
        "new": "taller/common/repuestos/repuesto_form.html",
    },
    {
        "file": "taller/views/country_aware_auth.py",
        "old": "taller/cl/es/account/login.html",
        "new": "cl/es/account/login.html",
    },
    {
        "file": "taller/views/country_aware_auth.py",
        "old": "taller/us/en/account/login.html",
        "new": "us/en/account/login.html",
    },
]


def move_file(src_rel: str, dst_rel: str, dry_run: bool = True):
    """Mueve un archivo de una ubicación a otra."""
    src = BASE_DIR / src_rel
    dst = BASE_DIR / dst_rel

    if not src.exists():
        print(f"[SKIP] No existe: {src}")
        return False

    print(f"{'DRY-RUN' if dry_run else 'MOVE   '} {src} -> {dst}")
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
    return True


def archive_path(rel_path: str, dry_run: bool = True):
    """Mueve una ruta completa a _archive."""
    src = BASE_DIR / rel_path
    if not src.exists():
        print(f"[SKIP] No existe: {src}")
        return

    dst = ARCHIVE_ROOT / rel_path
    print(f"{'DRY-RUN' if dry_run else 'ARCHIVE'} {src} -> {dst}")
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))


def update_code_references(dry_run: bool = True):
    """Actualiza referencias en archivos Python."""
    print("\n=== Actualizando referencias en código Python ===")
    for update in CODE_UPDATES:
        file_path = BASE_DIR / update["file"]
        if not file_path.exists():
            print(f"[SKIP] No existe: {file_path}")
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
            old_content = content

            # Reemplazar todas las ocurrencias
            content = content.replace(update["old"], update["new"])

            if content != old_content:
                print(f"{'DRY-RUN' if dry_run else 'UPDATE '} {file_path}")
                print(f"  '{update['old']}' -> '{update['new']}'")
                if not dry_run:
                    file_path.write_text(content, encoding="utf-8")
            else:
                print(f"[SKIP] No se encontró '{update['old']}' en {file_path}")
        except Exception as e:
            print(f"[ERROR] Error procesando {file_path}: {e}")


def main(dry_run: bool = True):
    print("=== Limpieza estructura final de templates ===")
    print(f"Archivo destino: {ARCHIVE_ROOT}\n")

    # 1. Mover archivos a nuevas ubicaciones
    print("=== 1. Moviendo archivos a nuevas ubicaciones ===")
    for move in MOVES:
        if move["type"] == "move":
            move_file(move["src"], move["dst"], dry_run=dry_run)

    # 2. Archivar carpetas completas
    print("\n=== 2. Archivando carpetas completas ===")
    for pattern in ARCHIVE_PATTERNS:
        archive_path(pattern, dry_run=dry_run)

    # 3. Archivar archivos legacy de repuestos
    print("\n=== 3. Archivando templates legacy de repuestos ===")
    for pattern in REPUESTO_LEGACY:
        archive_path(pattern, dry_run=dry_run)

    # 4. Actualizar referencias en código
    if not dry_run:
        update_code_references(dry_run=dry_run)
    else:
        print("\n=== 4. Referencias en código que se actualizarán ===")
        update_code_references(dry_run=True)


if __name__ == "__main__":
    # 1) Primero probar sin mover nada
    # main(dry_run=True)

    # Cuando estés conforme con la salida, comenta la línea anterior
    # y descomenta esta para ejecutar de verdad:
    main(dry_run=False)
