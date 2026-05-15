#!/usr/bin/env python
"""
Script para mostrar todas las URLs registradas en Django.
Útil para verificar que las URLs de ingreso-foto están disponibles.

Ejecutar: python manage.py shell < scripts/show_all_urls.py
O: python scripts/show_all_urls.py
"""
import os
import sys
import django

if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

django.setup()

from django.urls import get_resolver
from django.conf import settings

print("=" * 80)
print("LISTA COMPLETA DE URLs REGISTRADAS EN DJANGO")
print("=" * 80)
print()


def show_urls(urlconf, prefix="", indent=0):
    """Mostrar todas las URLs recursivamente"""
    resolver = get_resolver(urlconf)
    for pattern in resolver.url_patterns:
        if hasattr(pattern, "url_patterns"):
            # Es un include
            new_prefix = prefix + str(pattern.pattern)
            if hasattr(pattern, "namespace") and pattern.namespace:
                print(" " * indent + f"{prefix}{pattern.pattern} -> NAMESPACE: {pattern.namespace}")
            else:
                print(" " * indent + f"{prefix}{pattern.pattern} -> INCLUDE")
            show_urls(pattern.urlconf_name, new_prefix, indent + 2)
        else:
            # Es un path directo
            url_name = getattr(pattern, "name", "")
            callback_str = str(pattern.callback)
            if (
                "ingreso" in callback_str.lower()
                or "patente" in callback_str.lower()
                or "ingreso" in str(pattern.pattern)
            ):
                print(
                    " " * indent
                    + f">>> {prefix}{pattern.pattern} -> {callback_str} [name: {url_name}]"
                )
            elif "vehiculos" in str(pattern.pattern):
                print(
                    " " * indent + f"{prefix}{pattern.pattern} -> {callback_str} [name: {url_name}]"
                )


try:
    print("Buscando URLs relacionadas con 'ingreso', 'patente' y 'vehiculos':\n")
    show_urls(settings.ROOT_URLCONF)
    print("\n" + "=" * 80)
    print("Busqueda completada.")
except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
