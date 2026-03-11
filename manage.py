#!/usr/bin/env python
import os
import sys
import io
import logging

# Windows: forzar UTF-8 en stdout/stderr ANTES de cargar Django.
# Evita UnicodeEncodeError (ej. emoji ✅) al escribir en cp1252.
if os.name == "nt":
    os.environ.setdefault("PYTHONUTF8", "1")
    try:
        # Reconfigurar stdout y stderr con UTF-8 y manejo de errores
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        # Si reconfigure no está disponible (Python < 3.7), usar TextIOWrapper
        try:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
        except Exception:
            pass
    except Exception:
        pass


def main():
    # Usar settings_prod en producción (consistencia con Gunicorn); settings en desarrollo
    ENV = (os.getenv("DJANGO_ENV") or os.getenv("ENV") or "").lower()
    default_settings = (
        "gestion_taller.settings_prod"
        if ENV in ("prod", "production")
        else "gestion_taller.settings"
    )
    if ENV not in ("prod", "production"):
        logging.warning("Modo de desarrollo activado. Asegúrate de no usar esto en producción.")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", default_settings)

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
