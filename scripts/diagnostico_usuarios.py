#!/usr/bin/env python3
"""
Diagnóstico completo de usuarios y configuraciones
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_sqlite")
django.setup()

from django.contrib.auth.models import User

from taller.models.documento import Documento, RepuestoDocumento
from taller.models.empresa import Empresa
from taller.models.lineas_documento import LineaServicio
from taller.models.perfil_usuario import PerfilUsuario

print("🔍 === DIAGNÓSTICO USUARIOS Y CONFIGURACIONES ===")
print()

# Verificar usuarios existentes
users = User.objects.all()
print(f"👥 Total usuarios: {users.count()}")
for user in users:
    print(f"  - {user.username} (admin: {user.is_superuser}, staff: {user.is_staff})")

print()
print("👤 === PERFILES USUARIO ===")
perfiles = PerfilUsuario.objects.all()
print(f"Total perfiles: {perfiles.count()}")
for perfil in perfiles:
    print(f"  - {perfil.user.username}: {perfil.empresa.nombre_taller} ({perfil.rol})")

print()
print("🏢 === EMPRESAS ===")
empresas = Empresa.objects.all()
print(f"Total empresas: {empresas.count()}")
for empresa in empresas:
    usuario_asociado = empresa.usuario.username if empresa.usuario else "Ninguno"
    print(f"  - ID:{empresa.id} - {empresa.nombre_taller} (usuario: {usuario_asociado})")

print()
print("🔧 === VERIFICAR TALLER2 ===")
try:
    taller2 = User.objects.get(username="taller2")
    print(f"✅ Usuario taller2 encontrado: {taller2.username}")
    try:
        perfil = PerfilUsuario.objects.get(user=taller2)
        print(f"  - Perfil: {perfil.empresa.nombre_taller} ({perfil.rol})")
        print(f"  - Empresa ID: {perfil.empresa.id}")
        print(f"  - Es superadmin: {perfil.es_superadmin}")
    except PerfilUsuario.DoesNotExist:
        print("  - ❌ ERROR: No tiene PerfilUsuario asociado")
except User.DoesNotExist:
    print("❌ Usuario taller2 NO ENCONTRADO")

print()
print("📄 === DOCUMENTOS RECIENTES ===")
documentos = Documento.objects.all().order_by("-id")[:5]
for doc in documentos:
    repuestos_count = RepuestoDocumento.objects.filter(documento=doc).count()
    servicios_count = LineaServicio.objects.filter(documento=doc).count()
    print(
        f"  - Doc {doc.id}: {doc.empresa.nombre_taller} - R:{repuestos_count} S:{servicios_count}"
    )

print()
print("🎯 === USUARIOS SIN PERFIL ===")
users_sin_perfil = []
for user in users:
    try:
        PerfilUsuario.objects.get(user=user)
    except PerfilUsuario.DoesNotExist:
        users_sin_perfil.append(user.username)

if users_sin_perfil:
    print(f'❌ Usuarios sin PerfilUsuario: {", ".join(users_sin_perfil)}')
else:
    print("✅ Todos los usuarios tienen PerfilUsuario")

print()
print("🏁 === FIN DIAGNÓSTICO ===")
