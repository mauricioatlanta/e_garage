#!/usr/bin/env python3
"""
Verificación simple del sistema
"""
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.perfil_usuario import PerfilUsuario
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto as RepuestoDocumento, LineaServicio

print("🔍 === VERIFICACIÓN SISTEMA E-GARAGE ===")
print(f"📅 Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
print()

# 1. Estado general
print("1️⃣ ESTADO GENERAL:")
total_empresas = Empresa.objects.count()
total_usuarios = User.objects.count() 
total_perfiles = PerfilUsuario.objects.count()
total_documentos = Documento.objects.count()

print(f"   🏢 Empresas: {total_empresas}")
print(f"   👤 Usuarios: {total_usuarios}")
print(f"   📋 Perfiles: {total_perfiles}")
print(f"   📄 Documentos: {total_documentos}")

# 2. Verificar integridad
print()
print("2️⃣ VERIFICACIÓN INTEGRIDAD:")

usuarios_sin_perfil = 0
for user in User.objects.all():
    try:
        PerfilUsuario.objects.get(user=user)
    except PerfilUsuario.DoesNotExist:
        usuarios_sin_perfil += 1

if usuarios_sin_perfil == 0:
    print("   ✅ Todos los usuarios tienen perfil")
else:
    print(f"   ❌ {usuarios_sin_perfil} usuarios sin perfil")

# 3. Estado por empresa
print()
print("3️⃣ ESTADO POR EMPRESA:")
for empresa in Empresa.objects.all():
    docs = Documento.objects.filter(empresa=empresa)
    repuestos_total = RepuestoDocumento.objects.filter(documento__empresa=empresa).count()
    servicios_total = LineaServicio.objects.filter(documento__empresa=empresa).count()
    
    print(f"   🏢 {empresa.nombre_taller}:")
    print(f"      📄 Documentos: {docs.count()}")
    print(f"      📦 Repuestos: {repuestos_total}")
    print(f"      🔧 Servicios: {servicios_total}")

# 4. Documentos sin items
print()
print("4️⃣ DOCUMENTOS SIN ITEMS:")
docs_vacios = 0
for doc in Documento.objects.all():
    repuestos = RepuestoDocumento.objects.filter(documento=doc).count()
    servicios = LineaServicio.objects.filter(documento=doc).count()
    if repuestos == 0 and servicios == 0:
        docs_vacios += 1

if docs_vacios == 0:
    print("   ✅ Todos los documentos tienen items")
else:
    print(f"   ⚠️ {docs_vacios} documentos sin items")

# 5. Últimos documentos creados
print()
print("5️⃣ ÚLTIMOS DOCUMENTOS CREADOS:")
docs_recientes = Documento.objects.all().order_by('-pk')[:5]
for doc in docs_recientes:
    repuestos = RepuestoDocumento.objects.filter(documento=doc).count()
    servicios = LineaServicio.objects.filter(documento=doc).count()
    estado = "✅" if (repuestos > 0 and servicios > 0) else "⚠️" if (repuestos > 0 or servicios > 0) else "❌"
    print(f"   {estado} Doc {doc.pk}: {doc.numero_documento} ({doc.empresa.nombre_taller})")

print()
print("✅ VERIFICACIÓN COMPLETADA")

# Generar resumen en archivo
resumen_path = os.path.join(os.getcwd(), 'verificacion_sistema.txt')
with open(resumen_path, 'w', encoding='utf-8') as f:
    f.write(f"Verificación Sistema E-Garage - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    f.write("="*60 + "\n\n")
    f.write(f"Empresas: {total_empresas}\n")
    f.write(f"Usuarios: {total_usuarios}\n") 
    f.write(f"Perfiles: {total_perfiles}\n")
    f.write(f"Documentos: {total_documentos}\n")
    f.write(f"Usuarios sin perfil: {usuarios_sin_perfil}\n")
    f.write(f"Documentos vacíos: {docs_vacios}\n")

print(f"📁 Resumen guardado en: {resumen_path}")
print()
print("🏁 === FIN VERIFICACIÓN ===")
