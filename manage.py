#!/usr/bin/env python
import os
import sys
import logging


def main():
    """
    Entry point para comandos Django.
    - Respeta DJANGO_SETTINGS_MODULE si viene desde el entorno (systemd).
    - Solo muestra warning si DEBUG=True.
    """

    # No sobreescribir si ya viene definido (gunicorn/systemd o tu comando)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings_prod")

    try:
        from django.conf import settings
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Warning solo si realmente estamos en DEBUG
    if getattr(settings, "DEBUG", False):
        logging.warning(
            "Modo de desarrollo activado. Asegúrate de no usar esto en producción."
        )

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
