#!/usr/bin/env python
import logging
import os
import sys

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# 🔹 Punto de entrada principal del proyecto Django
def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

    # 🔍 Verificar dependencias clave (no importar paquetes opcionales pesados aquí)
    try:
        import django
    except ImportError as exc:
        logging.critical(
            "No se pudo importar Django. Asegúrate de haberlo instalado y de haber activado tu entorno virtual."
        )
        raise exc

    # Comprobar si estamos en modo de desarrollo
    if os.environ.get("DJANGO_SETTINGS_MODULE") == "gestion_taller.settings":
        logging.warning("Modo de desarrollo activado. Asegúrate de no usar esto en producción.")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        logging.critical(
            "No se pudo importar Django. Asegúrate de haberlo instalado y de haber activado tu entorno virtual."
        )
        raise exc

    # Log inicial
    logging.info("Iniciando servidor Django...")
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
