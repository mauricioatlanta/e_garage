#!/usr/bin/env python3
"""
Script para limpiar marcadores de conflicto de merge en taller/documentos/views.py
Ejecutar en el servidor: python3 limpiar_conflictos.py
"""
import os
import sys
import re

file_path = "taller/documentos/views.py"

if not os.path.exists(file_path):
    print(f"❌ Archivo no encontrado: {file_path}")
    sys.exit(1)

print(f"📄 Procesando {file_path}...")

# Leer el archivo
try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
except Exception as e:
    print(f"❌ Error al leer archivo: {e}")
    sys.exit(1)

# Verificar si hay marcadores de conflicto
has_conflicts = False
if "<<<<<<<" in content or "=======" in content or ">>>>>>>" in content:
    has_conflicts = True
    print("⚠️  Marcadores de conflicto encontrados")

    # Crear backup
    backup_path = f"{file_path}.backup"
    try:
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📦 Backup creado: {backup_path}")
    except Exception as e:
        print(f"⚠️  No se pudo crear backup: {e}")

    # Eliminar líneas con marcadores de conflicto
    lines = content.split("\n")
    new_lines = []
    removed_count = 0

    for line in lines:
        # Detectar marcadores de conflicto
        if (
            re.match(r"^<<<<<<<", line)
            or re.match(r"^=======$", line)
            or re.match(r"^>>>>>>>", line)
        ):
            removed_count += 1
            continue
        new_lines.append(line)

    new_content = "\n".join(new_lines)

    if removed_count > 0:
        print(f"✅ Eliminadas {removed_count} líneas con marcadores de conflicto")

        # Escribir el archivo limpio
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"✅ Archivo actualizado")
        except Exception as e:
            print(f"❌ Error al escribir archivo: {e}")
            sys.exit(1)

        # Verificar sintaxis
        try:
            compile(new_content, file_path, "exec")
            print("✅ Sintaxis Python válida")
        except SyntaxError as e:
            print(f"❌ Error de sintaxis: {e}")
            print("🔄 Restaurando desde backup...")
            try:
                with open(backup_path, "r", encoding="utf-8") as f:
                    backup_content = f.read()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(backup_content)
                print("✅ Archivo restaurado desde backup")
            except Exception as e2:
                print(f"❌ Error al restaurar: {e2}")
            sys.exit(1)
    else:
        print("ℹ️  No se encontraron líneas para eliminar")
else:
    print("✅ No se encontraron marcadores de conflicto")

print("\n✅ Proceso completado")
print("\n💡 Recuerda reiniciar el servidor WSGI:")
print("   touch /var/www/www_egarage_cl_wsgi.py")
