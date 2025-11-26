import os
import shutil
from pathlib import Path

# Cambia esto a la ruta raíz de tu proyecto
BASE_DIR = Path(r"E:\projecto\e_garage")

MANUAL_MAPPING = {
    # account por país
    "templates/account/login_peru.html": "templates/pe/es/account/login.html",
    "templates/account/login_venezuela.html": "templates/ve/es/account/login.html",
    "templates/account/signup_peru.html": "templates/pe/es/account/signup.html",
    "templates/account/signup_venezuela.html": "templates/ve/es/account/signup.html",
    "templates/account/signup_brasil.html": "templates/br/es/account/signup.html",
    # onboarding por país
    "templates/onboarding/bienvenida_chile.html": "templates/cl/es/onboarding/bienvenida.html",
    "templates/onboarding/bienvenida_peru.html": "templates/pe/es/onboarding/bienvenida.html",
    "templates/onboarding/bienvenida_colombia.html": "templates/co/es/onboarding/bienvenida.html",
    "templates/onboarding/bienvenida_ecuador.html": "templates/ec/es/onboarding/bienvenida.html",
    "templates/onboarding/bienvenida_venezuela.html": "templates/ve/es/onboarding/bienvenida.html",
    "templates/onboarding/bienvenida_brasil.html": "templates/br/es/onboarding/bienvenida.html",
    "templates/onboarding/bienvenida_usa.html": "templates/us/es/onboarding/bienvenida.html",
    # suscripción pagos
    "templates/suscripcion/pago_chile.html": "templates/cl/es/suscripcion/pago.html",
    "templates/suscripcion/pago_mexico.html": "templates/mx/es/suscripcion/pago.html",
    "templates/suscripcion/pago_usa.html": "templates/us/en/suscripcion/pago.html",
    # landing USA
    "templates/landing/usa.html": "templates/us/en/landing/usa.html",
    "templates/landing/usa_landing.html": "templates/us/en/landing/usa_landing.html",
    "templates/us/en/landing_usa.html": "templates/us/en/landing/landing_usa.html",
    # dashboards: NO MOVER - el usuario se encargará de revisarlos y borrarlos
    # "templates/cl/dashboard_chile.html": "templates/cl/es/dashboard/centro_operaciones_espacial.html",
}


def move_with_dirs(src: Path, dst: Path, dry_run: bool = True):
    if not src.exists():
        print(f"[WARN] No existe: {src}")
        return

    if dst.exists():
        print(f"[WARN] DESTINO YA EXISTE, no muevo: {dst}")
        return

    print(f"{'DRY-RUN ' if dry_run else 'MOVE    '} {src} -> {dst}")
    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))


def aplicar_manual(dry_run: bool = True):
    print("=== MAPEOS MANUALES POR PAÍS ===")
    for old, new in MANUAL_MAPPING.items():
        src = BASE_DIR / old
        dst = BASE_DIR / new
        move_with_dirs(src, dst, dry_run=dry_run)


def mover_taller_por_pais(dry_run: bool = True):
    print("=== MOVER templates/taller/cl/* -> templates/cl/* ===")
    for path in BASE_DIR.rglob("templates/taller/cl/*"):
        if path.is_dir():
            continue
        rel = path.relative_to(BASE_DIR)
        new_rel = Path(str(rel).replace("templates/taller/cl/", "templates/cl/"))
        dst = BASE_DIR / new_rel
        move_with_dirs(path, dst, dry_run=dry_run)

    print("=== MOVER templates/taller/us/* -> templates/us/* ===")
    for path in BASE_DIR.rglob("templates/taller/us/*"):
        if path.is_dir():
            continue
        rel = path.relative_to(BASE_DIR)
        new_rel = Path(str(rel).replace("templates/taller/us/", "templates/us/"))
        dst = BASE_DIR / new_rel
        move_with_dirs(path, dst, dry_run=dry_run)


if __name__ == "__main__":
    # PRIMER PASO: ver solo qué haría (sin mover nada)
    aplicar_manual(dry_run=True)
    mover_taller_por_pais(dry_run=True)

    # Cuando estés conforme, cambia a False y vuelve a ejecutar:
    # aplicar_manual(dry_run=False)
    # mover_taller_por_pais(dry_run=False)
