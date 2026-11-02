#!/usr/bin/env python
"""
Script final de verificación para el problema de la bandera
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.models import Empresa


def main():
    print("=== VERIFICACIÓN FINAL DEL PROBLEMA DE LA BANDERA ===")

    try:
        user = User.objects.get(username="testuser_usa")
        empresa = Empresa.objects.get(user=user)

        print(f"✓ Usuario: {user.username}")
        print(f"✓ Empresa: {empresa.nombre_taller}")
        print(f"✓ País de la empresa: {empresa.pais}")

        # Verificar qué debería mostrarse
        expected_flag = "🇺🇸" if empresa.pais == "US" else "🇨🇱"
        expected_country = "USA" if empresa.pais == "US" else "Chile"

        print("\n📋 RESULTADO ESPERADO:")
        print(f"  - Bandera: {expected_flag}")
        print(f"  - País: {expected_country}")
        print(f"  - Selector de idioma: {expected_flag} ES / {expected_flag} EN")

        if empresa.pais == "US":
            print("\n✅ CORRECTO: El usuario debería ver la bandera de Estados Unidos")
        else:
            print(f"\n❌ PROBLEMA: El país debería ser 'US' pero es '{empresa.pais}'")

        # Mostrar instrucciones
        print("\n🔗 PARA VERIFICAR:")
        print(f"1. Iniciar sesión como: {user.username}")
        print("2. Ir a: http://127.0.0.1:8000/us/clientes/")
        print(f"3. Verificar que aparezca: {expected_flag} ES en el selector de idioma")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
