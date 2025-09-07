#!/usr/bin/env python
"""
Script para corregir la configuración del país del usuario testuser_usa
"""
import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.models import Empresa


def main():
    print("=== CORRECCIÓN DEL PAÍS PARA TESTUSER_USA ===")

    try:
        user = User.objects.get(username="testuser_usa")
        print(f"✓ Usuario encontrado: {user.username}")

        # Obtener o crear empresa
        try:
            empresa = Empresa.objects.get(user=user)
            print(f"✓ Empresa encontrada: {empresa.nombre_taller}")
            print(f"  País actual: {getattr(empresa, 'pais', 'No definido')}")

            # Corregir el país
            empresa.pais = "US"
            empresa.save()

            print(f"✅ País corregido a: {empresa.pais}")

        except Empresa.DoesNotExist:
            print("❌ No se encontró empresa para el usuario")
            print("Creando empresa para USA...")

            empresa = Empresa.objects.create(
                user=user, nombre_taller="USA Test Garage", pais="US"
            )
            print(f"✅ Empresa creada: {empresa.nombre_taller} (País: {empresa.pais})")

        # Verificar otros usuarios USA para comparación
        print("\n=== VERIFICACIÓN OTROS USUARIOS USA ===")
        empresas_usa = Empresa.objects.filter(pais="US")
        print(f"Empresas con país US: {empresas_usa.count()}")

        for emp in empresas_usa:
            print(f"  - {emp.nombre_taller} (Usuario: {emp.user.username})")

    except User.DoesNotExist:
        print("❌ Usuario testuser_usa no existe")


if __name__ == "__main__":
    main()
