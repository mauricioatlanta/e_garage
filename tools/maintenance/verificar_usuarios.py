#!/usr/bin/env python
"""
Script para verificar usuarios existentes
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User


def verificar_usuarios():
    """Verifica qué usuarios existen en la base de datos"""
    print("👥 VERIFICANDO USUARIOS EXISTENTES")
    print("=" * 60)

    usuarios = User.objects.all()

    print(f"📊 Total usuarios: {usuarios.count()}")

    for usuario in usuarios:
        print(f"   👤 {usuario.username}")
        print(f"      • Email: {usuario.email}")
        print(f"      • Activo: {usuario.is_active}")
        print(f"      • Staff: {usuario.is_staff}")

        # Verificar si tiene empresa
        if hasattr(usuario, "empresa") and usuario.empresa:
            print(f"      • Empresa: {usuario.empresa.nombre_taller}")
            print(f"      • País: {usuario.empresa.pais}")
        else:
            print("      • Empresa: Sin empresa")
        print()

    print("✅ VERIFICACIÓN COMPLETADA!")


if __name__ == "__main__":
    verificar_usuarios()
