#!/usr/bin/env python
"""
Script directo para corregir definitivamente el país del usuario testuser_usa
"""

import os
import sys

import django

# Configurar el path y Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.models import Empresa


def main():
    print("=== CORRECCIÓN DEFINITIVA DEL PAÍS ===")

    try:
        # Obtener usuario
        user = User.objects.get(username="testuser_usa")
        print(f"✓ Usuario encontrado: {user.username}")

        # Obtener empresa
        try:
            empresa = Empresa.objects.get(user=user)
        except Empresa.DoesNotExist:
            # Buscar por campo legacy
            empresa = Empresa.objects.filter(usuario=user).first()
            if not empresa:
                print("❌ No se encontró empresa, creando una nueva...")
                empresa = Empresa.objects.create(
                    user=user, nombre_taller="USA Test Garage", pais="US"
                )

        print(f"✓ Empresa: {empresa.nombre_taller}")
        print(f"  País actual: {empresa.pais}")

        # Forzar cambio a US
        if empresa.pais != "US":
            print("🔧 Cambiando país a US...")
            empresa.pais = "US"
            empresa.save()
            print("✅ País cambiado a US")

        # Verificar que se guardó
        empresa.refresh_from_db()
        print(f"  País después del cambio: {empresa.pais}")

        # Verificar otros campos que puedan afectar
        if hasattr(empresa, "country"):
            print(f"  Campo country: {getattr(empresa, 'country', 'No existe')}")
        if hasattr(empresa, "region"):
            print(f"  Campo region: {getattr(empresa, 'region', 'No existe')}")
        if hasattr(empresa, "configuracion_regional"):
            print(
                f"  Configuración regional: {getattr(empresa, 'configuracion_regional', 'No existe')}"
            )

        print("\n🎯 RESULTADO FINAL:")
        print(f"  Usuario: {user.username}")
        print(f"  Empresa: {empresa.nombre_taller}")
        print(f"  País: {empresa.pais}")

        if empresa.pais == "US":
            print("✅ ¡CORRECTO! Debería mostrar bandera de USA 🇺🇸")
        else:
            print("❌ PROBLEMA PERSISTE")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
