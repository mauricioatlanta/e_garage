#!/usr/bin/env python
"""
Script de diagnóstico para verificar el estado del logo en CompanySettings
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "e_garage.settings")
django.setup()

from django.contrib.auth.models import User
from taller.models.company_settings import CompanySettings

print("=" * 60)
print("DIAGNÓSTICO DE LOGO EN COMPANY SETTINGS")
print("=" * 60)

# Obtener todos los usuarios con CompanySettings
users_with_settings = User.objects.filter(company_settings__isnull=False).distinct()

if not users_with_settings.exists():
    print("\n❌ No se encontraron usuarios con CompanySettings")
else:
    print(f"\n✅ Se encontraron {users_with_settings.count()} usuario(s) con CompanySettings\n")

    for user in users_with_settings:
        print(f"Usuario: {user.username} (ID: {user.id})")
        try:
            cs = CompanySettings.objects.filter(user=user).order_by("-updated_at").first()
            if cs:
                print(f"  - CompanySettings ID: {cs.id}")
                print(f"  - Nombre empresa: {cs.company_name}")
                print(f"  - Tiene logo: {bool(cs.logo)}")

                if cs.logo:
                    print(f"  - Logo name: {cs.logo.name}")
                    try:
                        print(f"  - Logo URL: {cs.logo.url}")
                        # Verificar si el archivo existe
                        if hasattr(cs.logo, "path"):
                            import os

                            if os.path.exists(cs.logo.path):
                                print(f"  - ✅ Archivo existe físicamente: {cs.logo.path}")
                            else:
                                print(f"  - ❌ Archivo NO existe: {cs.logo.path}")
                    except Exception as e:
                        print(f"  - ❌ Error obteniendo URL: {e}")
                else:
                    print(f"  - ⚠️ No tiene logo asignado")
                print(f"  - Última actualización: {cs.updated_at}")
                print()
            else:
                print(f"  - ❌ No se encontró CompanySettings")
        except Exception as e:
            print(f"  - ❌ Error: {e}")
        print("-" * 60)

print("\n" + "=" * 60)
print("FIN DEL DIAGNÓSTICO")
print("=" * 60)
