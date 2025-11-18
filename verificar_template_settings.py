#!/usr/bin/env python
"""
Script para verificar si el template existe en el servidor
"""
import os

# Ruta donde Django busca el template
template_path = "/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg/templates/taller/us/en/settings/futuristic_company_settings.html"

print("=" * 70)
print("VERIFICACIÓN DEL TEMPLATE EN EL SERVIDOR")
print("=" * 70)

# Verificar si el archivo existe
if os.path.exists(template_path):
    print(f"✅ El archivo EXISTE en: {template_path}")

    # Verificar el tamaño del archivo
    file_size = os.path.getsize(template_path)
    print(f"   Tamaño del archivo: {file_size} bytes")

    if file_size == 0:
        print("   ⚠️  El archivo está VACÍO (0 bytes)")
        print("   Necesitas pegar el contenido completo del template.")
    else:
        print(f"   ✅ El archivo tiene contenido ({file_size} bytes)")

        # Leer las primeras líneas para verificar
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                first_lines = f.readlines()[:5]
                print("\n   Primeras líneas del archivo:")
                for i, line in enumerate(first_lines, 1):
                    print(f"   {i}: {line.strip()[:80]}")
        except Exception as e:
            print(f"   ❌ Error al leer el archivo: {e}")
else:
    print(f"❌ El archivo NO EXISTE en: {template_path}")
    print("\n   Verificando si el directorio existe...")

    # Verificar si el directorio existe
    dir_path = os.path.dirname(template_path)
    if os.path.exists(dir_path):
        print(f"   ✅ El directorio existe: {dir_path}")
        print(f"   Archivos en el directorio:")
        try:
            files = os.listdir(dir_path)
            for f in files:
                print(f"      - {f}")
        except Exception as e:
            print(f"   ❌ Error al listar archivos: {e}")
    else:
        print(f"   ❌ El directorio NO existe: {dir_path}")
        print(f"   Necesitas crear el directorio primero.")

print("\n" + "=" * 70)
print("FIN")
print("=" * 70)
