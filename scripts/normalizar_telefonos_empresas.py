"""
Script de Migración: Normalizar Números de Teléfono de Empresas

Este script normaliza todos los números de teléfono en la base de datos,
asegurando que tengan el prefijo "+" según el país de cada empresa.

USO:
    python manage.py shell
    >>> exec(open('scripts/normalizar_telefonos_empresas.py').read())

    O directamente:
    python manage.py shell < scripts/normalizar_telefonos_empresas.py
"""

import os
import django

# Configurar Django (si no se ejecuta desde manage.py shell)
if "DJANGO_SETTINGS_MODULE" not in os.environ:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
    django.setup()

from taller.models.empresa import Empresa
from taller.config.country_settings import CountrySettings
from taller.utils.validators import normalizar_telefono_con_prefijo


def normalizar_telefonos_empresas():
    """
    Recorre todas las empresas registradas y normaliza sus números de teléfono.

    Para cada empresa que tenga un número de teléfono sin prefijo "+",
    se le antepone el prefijo correspondiente según su país registrado.
    """
    empresas_actualizadas = 0
    empresas_con_errores = 0

    print("=" * 60)
    print("NORMALIZACIÓN DE NÚMEROS DE TELÉFONO")
    print("=" * 60)
    print()

    # Recorrer todas las empresas
    empresas = Empresa.objects.all()
    total_empresas = empresas.count()

    print(f"Total de empresas a revisar: {total_empresas}")
    print()

    for emp in empresas:
        if not emp.telefono:
            # Empresa sin teléfono, saltar
            continue

        # Obtener teléfono original
        telefono_original = emp.telefono.strip()

        # Si ya tiene prefijo "+", verificar si está bien formateado
        if telefono_original.startswith("+"):
            # Ya tiene prefijo, pero verificar que esté normalizado correctamente
            telefono_normalizado = normalizar_telefono_con_prefijo(telefono_original, emp.pais)

            if telefono_normalizado != telefono_original:
                # El número necesita normalización (puede tener espacios, guiones, etc.)
                print(f"Normalizando: {emp.nombre_taller}")
                print(f"  Original: {telefono_original}")
                print(f"  Normalizado: {telefono_normalizado}")
                emp.telefono = telefono_normalizado
                emp.save(update_fields=["telefono"])
                empresas_actualizadas += 1
                print()
        else:
            # NO tiene prefijo "+", necesita normalización
            try:
                # Obtener el prefijo según su país registrado
                config = CountrySettings.get_country_config(emp.pais)
                prefijo = config.get("phone_prefix", "")

                # Normalizar el número
                telefono_normalizado = normalizar_telefono_con_prefijo(telefono_original, emp.pais)

                print(f"Reparando: {emp.nombre_taller} ({emp.pais})")
                print(f"  Original: {telefono_original}")
                print(f"  Prefijo del país: {prefijo}")
                print(f"  Normalizado: {telefono_normalizado}")

                # Actualizar en la base de datos
                emp.telefono = telefono_normalizado
                emp.save(update_fields=["telefono"])
                empresas_actualizadas += 1
                print()

            except Exception as e:
                empresas_con_errores += 1
                print(f"❌ ERROR al normalizar {emp.nombre_taller}: {e}")
                print(f"   Teléfono original: {telefono_original}")
                print(f"   País: {emp.pais}")
                print()

    # Resumen final
    print("=" * 60)
    print("RESUMEN DE NORMALIZACIÓN")
    print("=" * 60)
    print(f"Total de empresas revisadas: {total_empresas}")
    print(f"Empresas actualizadas: {empresas_actualizadas}")
    print(f"Empresas con errores: {empresas_con_errores}")
    print()
    print("✅ Proceso completado")
    print("=" * 60)


# Ejecutar la función si se ejecuta directamente
if __name__ == "__main__" or __name__ == "__builtin__":
    normalizar_telefonos_empresas()
