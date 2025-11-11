#!/usr/bin/env python3
"""
Script de verificación para la restricción de usuario único por empresa
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "e_garage.settings")
django.setup()

from django.contrib.auth.models import User

from taller.models.empresa import Empresa
from taller.models.perfilusuario import PerfilUsuario


def verificar_restriccion_usuario_unico():
    """
    Verificar que la restricción de usuario único por empresa funciona correctamente
    """
    print("🔍 VERIFICACIÓN: Restricción de Usuario Único por Empresa")
    print("=" * 60)

    # 1. Verificar modelo Empresa
    print("\n1️⃣ Verificando modelo Empresa...")
    empresas = Empresa.objects.all()
    print(f"   📊 Total de empresas: {empresas.count()}")

    for empresa in empresas:
        print(f"   ✅ {empresa.nombre_taller} -> Usuario: {empresa.user.username}")

    # 2. Verificar que no hay duplicados
    print("\n2️⃣ Verificando usuarios únicos...")
    users_count = User.objects.filter(empresa__isnull=False).count()
    empresas_count = Empresa.objects.count()

    if users_count == empresas_count:
        print(f"   ✅ Relación 1:1 correcta: {users_count} usuarios = {empresas_count} empresas")
    else:
        print(f"   ❌ ERROR: {users_count} usuarios ≠ {empresas_count} empresas")

    # 3. Verificar PerfilUsuario (debe estar limitado)
    print("\n3️⃣ Verificando PerfilUsuario...")
    perfiles = PerfilUsuario.objects.all()
    print(f"   📊 Total de perfiles de usuario: {perfiles.count()}")

    if perfiles.count() == 0:
        print("   ✅ No hay perfiles de usuario adicionales (correcto)")
    else:
        print("   ⚠️  Existen perfiles de usuario adicionales")
        for perfil in perfiles:
            print(f"      - {perfil.user.username} en {perfil.empresa.nombre_taller}")

    # 4. Probar creación de empresa duplicada
    print("\n4️⃣ Probando restricciones...")
    try:
        # Intentar crear una segunda empresa para un usuario existente
        user_existente = User.objects.first()
        if user_existente:
            nueva_empresa = Empresa(user=user_existente, nombre_taller="Empresa Duplicada")
            nueva_empresa.save()
            print("   ❌ ERROR: Se permitió crear empresa duplicada")
        else:
            print("   ⚠️  No hay usuarios para probar")
    except Exception as e:
        print(f"   ✅ Restricción funciona: {str(e)}")

    print("\n" + "=" * 60)
    print("✅ VERIFICACIÓN COMPLETADA")


if __name__ == "__main__":
    verificar_restriccion_usuario_unico()
