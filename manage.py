#!/usr/bin/env python
import os
import sys
import logging
from pathlib import Path


def main():
    # Cargar .env.prod si existe (antes de verificar EGARAGE_ENV)
    try:
        from dotenv import load_dotenv

        env_prod_path = Path(__file__).resolve().parent / ".env.prod"
        if env_prod_path.exists():
            load_dotenv(env_prod_path, override=True)
    except ImportError:
        pass

    # Warning solo en desarrollo
    if os.getenv("EGARAGE_ENV", "dev").lower() != "prod":
        logging.warning("Modo de desarrollo activado. Asegúrate de no usar esto en producción.")

    # Usar settings_prod por defecto (producción), permitir override para desarrollo local
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings_prod")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
