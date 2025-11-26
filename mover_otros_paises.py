"""
Script para mover archivos de otros países (PE, CO, EC, VE, BR, MX) a sus ubicaciones correctas.
Basado en el mapeo de reordenar_templates.py
"""

import shutil
from pathlib import Path

BASE_DIR = Path(r"E:\projecto\e_garage")

# Mapeo de archivos por país (del script reordenar_templates.py)
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
}

print("=" * 80)
print("MOVIENDO ARCHIVOS DE OTROS PAÍSES")
print("=" * 80)

moved = 0
skipped = 0
not_found = 0

for src_path, dst_path in MANUAL_MAPPING.items():
    src = BASE_DIR / src_path
    dst = BASE_DIR / dst_path

    if not src.exists():
        print(f"[NOT FOUND] {src_path}")
        not_found += 1
        continue

    if dst.exists():
        print(f"[SKIP] Ya existe: {dst_path}")
        skipped += 1
        continue

    print(f"[MOVE] {src_path} -> {dst_path}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    moved += 1

print("\n" + "=" * 80)
print(f"Movidos: {moved}, Omitidos: {skipped}, No encontrados: {not_found}")
print("=" * 80)
