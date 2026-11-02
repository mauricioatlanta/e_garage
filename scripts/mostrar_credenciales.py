#!/usr/bin/env python
"""
Script para mostrar credenciales de prueba
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User


def main():
    print("🔐 CREDENCIALES DE PRUEBA - eGARAGE")
    print("=" * 50)

    # Usuarios principales de prueba
    usuarios_prueba = [
        ("admin_chile", "admin123", "Chile"),
        ("admin_usa", "admin123", "USA"),
        ("testuser_usa", "TestUSA2025!", "USA"),
        ("testuser_cl", "test123", "Chile"),
        ("admin", "admin123", "General"),
        ("test_diagnostic", "test123", "Diagnóstico"),
    ]

    print("\n🇨🇱 CHILE - Credenciales:")
    print("-" * 30)
    for username, password, pais in usuarios_prueba:
        if pais == "Chile":
            try:
                user = User.objects.get(username=username)
                try:
                    empresa = user.empresa
                    print(f"✓ Usuario: {username}")
                    print(f"  Contraseña: {password}")
                    print(f"  Empresa: {empresa.nombre_taller}")
                    print(f"  País: {empresa.pais}")
                    print()
                except:
                    print(f"✓ Usuario: {username}")
                    print(f"  Contraseña: {password}")
                    print("  Estado: Sin empresa")
                    print()
            except User.DoesNotExist:
                print(f"✗ Usuario: {username} - No existe")

    print("\n🇺🇸 USA - Credenciales:")
    print("-" * 30)
    for username, password, pais in usuarios_prueba:
        if pais == "USA":
            try:
                user = User.objects.get(username=username)
                try:
                    empresa = user.empresa
                    print(f"✓ Usuario: {username}")
                    print(f"  Contraseña: {password}")
                    print(f"  Empresa: {empresa.nombre_taller}")
                    print(f"  País: {empresa.pais}")
                    print()
                except:
                    print(f"✓ Usuario: {username}")
                    print(f"  Contraseña: {password}")
                    print("  Estado: Sin empresa")
                    print()
            except User.DoesNotExist:
                print(f"✗ Usuario: {username} - No existe")

    print("\n🌍 URLS DE ACCESO:")
    print("-" * 30)
    print("🇨🇱 Chile: http://127.0.0.1:8000/cl/")
    print("🇺🇸 USA: http://127.0.0.1:8000/us/")
    print("🔑 Login: http://127.0.0.1:8000/accounts/login/")
    print("⚙️ Admin: http://127.0.0.1:8000/admin/")

    print("\n📱 ACCESO DIRECTO:")
    print("-" * 30)
    print("Chile - Clientes: http://127.0.0.1:8000/cl/clientes/")
    print("Chile - Vehículos: http://127.0.0.1:8000/cl/vehiculos/")
    print("Chile - Documentos: http://127.0.0.1:8000/cl/documentos/")
    print()
    print("USA - Clientes: http://127.0.0.1:8000/us/clientes/")
    print("USA - Vehículos: http://127.0.0.1:8000/us/vehiculos/")
    print("USA - Documentos: http://127.0.0.1:8000/us/documentos/")

    print("\n💡 RECOMENDACIONES:")
    print("-" * 30)
    print("• Para Chile: Usar admin_chile / admin123")
    print("• Para USA: Usar admin_usa / admin123")
    print("• Usuario alternativo USA: testuser_usa / TestUSA2025!")
    print("• El sistema detecta automáticamente el país por la URL (/cl/ o /us/)")


if __name__ == "__main__":
    main()
