#!/usr/bin/env python
import os
import sys
import logging


def main():
    # Warning solo en desarrollo (no en producción)
    ENV = (os.getenv("DJANGO_ENV") or os.getenv("ENV") or "").lower()
    if ENV not in ("prod", "production"):
        logging.warning("Modo de desarrollo activado. Asegúrate de no usar esto en producción.")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

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
