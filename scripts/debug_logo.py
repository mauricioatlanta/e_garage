"""
Script de diagnóstico para verificar por qué el logo no aparece
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User
from taller.models.company_settings import CompanySettings

# Buscar usuarios con CompanySettings
print("=" * 60)
print("DIAGNÓSTICO DE LOGOS")
print("=" * 60)

users_with_settings = User.objects.filter(company_settings__isnull=False).distinct()
print(f"\nUsuarios con CompanySettings: {users_with_settings.count()}")

for user in users_with_settings[:10]:  # Limitar a 10
    try:
        settings = CompanySettings.objects.filter(user=user).first()
        if settings:
            print(f"\n--- Usuario: {user.username} ---")
            print(f"  Company Name: {settings.company_name}")
            print(f"  Tiene logo: {bool(settings.logo)}")
            if settings.logo:
                try:
                    print(
                        f"  Logo path: {settings.logo.path if hasattr(settings.logo, 'path') else 'N/A'}"
                    )
                    print(f"  Logo URL: {settings.logo.url}")
                    print(f"  Logo name: {settings.logo.name}")
                except Exception as e:
                    print(f"  ERROR obteniendo logo: {e}")
            else:
                print("  ⚠️ NO TIENE LOGO")
    except Exception as e:
        print(f"Error procesando usuario {user.username}: {e}")

print("\n" + "=" * 60)
print("FIN DEL DIAGNÓSTICO")
print("=" * 60)
