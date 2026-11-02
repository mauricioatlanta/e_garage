#!/usr/bin/env python
import sys

# ── Guardia de versión Python ──────────────────────────────────────────────────
# Django 4.2 solo soporta Python 3.8–3.12. Python 3.13+ rompe Context.__copy__
# en el sistema de templates y el cliente de pruebas (store_rendered_templates),
# causando fallos en tests y comportamiento indefinido en producción.
_PY = sys.version_info
if not ((3, 11) <= _PY < (3, 13)):
    sys.stderr.write(
        f"\n[eGarage] Python {_PY.major}.{_PY.minor} no está soportado.\n"
        "         Versiones requeridas: 3.11 o 3.12.\n\n"
        "         Para recrear el entorno virtual:\n"
        "           pyenv install 3.12        # o: sudo apt install python3.12\n"
        "           pyenv local 3.12\n"
        "           rm -rf .venv\n"
        "           python3.12 -m venv .venv\n"
        "           source .venv/bin/activate\n"
        "           pip install -r requirements.txt\n\n"
    )
    sys.exit(1)
# ── Fin guardia ────────────────────────────────────────────────────────────────

import os
from pathlib import Path

from dotenv import load_dotenv


def main():
    base_dir = Path(__file__).resolve().parent

    env_name = os.getenv("EGARAGE_ENV", "dev").lower()

    if env_name == "prod":
        env_prod = base_dir / ".env.prod"
        if env_prod.exists():
            load_dotenv(env_prod, override=True)
        os.environ["DJANGO_SETTINGS_MODULE"] = "gestion_taller.settings_prod"
    else:
        env_local = base_dir / ".env"
        if env_local.exists():
            load_dotenv(env_local, override=True)
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
