#!/usr/bin/env python
"""
Script para forzar el cambio de país directamente en SQL
"""

import os
import sys

import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User
from django.db import connection

from taller.models import Empresa


def main():
    print("=== FORZAR CAMBIO DE PAÍS CON SQL ===")

    # Obtener ID del usuario
    try:
        user = User.objects.get(username="testuser_usa")
        print(f"✓ Usuario ID: {user.id}")

        # Buscar empresa por user_id
        empresas = Empresa.objects.filter(user_id=user.id)
        print(f"✓ Empresas encontradas por user_id: {empresas.count()}")

        for empresa in empresas:
            print(f"  - Empresa: {empresa.nombre_taller} (País: {empresa.pais})")
            empresa.pais = "US"
            empresa.save()
            print(f"    → Cambiado a: {empresa.pais}")

        # Buscar empresa por usuario_id (campo legacy)
        empresas_legacy = Empresa.objects.filter(usuario_id=user.id)
        print(f"✓ Empresas encontradas por usuario_id: {empresas_legacy.count()}")

        for empresa in empresas_legacy:
            print(
                f"  - Empresa (legacy): {empresa.nombre_taller} (País: {empresa.pais})"
            )
            empresa.pais = "US"
            empresa.save()
            print(f"    → Cambiado a: {empresa.pais}")

        # Verificar con SQL directo
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, nombre_taller, pais, user_id, usuario_id FROM taller_empresa WHERE user_id = %s OR usuario_id = %s",
                [user.id, user.id],
            )
            rows = cursor.fetchall()
            print("\n✓ Verificación SQL directa:")
            for row in rows:
                print(
                    f"  - ID: {row[0]}, Nombre: {row[1]}, País: {row[2]}, user_id: {row[3]}, usuario_id: {row[4]}"
                )

                # Forzar actualización SQL
                cursor.execute(
                    "UPDATE taller_empresa SET pais = 'US' WHERE id = %s", [row[0]]
                )
                print("    → SQL UPDATE aplicado")

        print("\n✅ Cambios aplicados con SQL directo")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
