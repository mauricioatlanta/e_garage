#!/usr/bin/env python3
"""
Script para corregir taller/documentos/views.py en el servidor
Ejecutar: python3 fix_views_servidor.py
"""
import os
import sys
import subprocess

file_path = "taller/documentos/views.py"

print("=" * 60)
print("CORRECCIÓN DE taller/documentos/views.py EN SERVIDOR")
print("=" * 60)

# Verificar que estamos en el directorio correcto
if not os.path.exists(file_path):
    print(f"❌ Error: {file_path} no encontrado")
    print(f"   Directorio actual: {os.getcwd()}")
    print(f"   Cambia al directorio del proyecto primero:")
    print(f"   cd /home/atlantareciclajes/apps/egarage/current")
    sys.exit(1)

print(f"\n📄 Archivo encontrado: {file_path}")

# Leer el archivo
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"✅ Archivo leído ({len(content)} caracteres)")
except Exception as e:
    print(f"❌ Error al leer archivo: {e}")
    sys.exit(1)

# Verificar si hay marcadores de conflicto
has_conflicts = '<<<<<<<' in content or '=======' in content or '>>>>>>>' in content

if has_conflicts:
    print("\n⚠️  MARCADORES DE CONFLICTO DETECTADOS")
    print("   Intentando restaurar desde Git...")
    
    # Crear backup
    backup_path = f"{file_path}.backup"
    try:
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📦 Backup creado: {backup_path}")
    except Exception as e:
        print(f"⚠️  No se pudo crear backup: {e}")
    
    # Intentar restaurar desde Git
    try:
        result = subprocess.run(
            ['git', 'checkout', 'HEAD', '--', file_path],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(file_path)) or '.'
        )
        
        if result.returncode == 0:
            print("✅ Archivo restaurado desde Git (HEAD)")
            
            # Verificar que se restauró correctamente
            with open(file_path, 'r', encoding='utf-8') as f:
                new_content = f.read()
            
            if '<<<<<<<' not in new_content and '=======' not in new_content and '>>>>>>>' not in new_content:
                print("✅ Sin marcadores de conflicto después de restaurar")
            else:
                print("⚠️  Aún hay marcadores de conflicto después de restaurar")
                print("   Intentando desde origin/main...")
                
                # Intentar desde origin/main
                result2 = subprocess.run(
                    ['git', 'fetch', 'origin', 'main'],
                    capture_output=True,
                    text=True
                )
                
                result3 = subprocess.run(
                    ['git', 'checkout', 'origin/main', '--', file_path],
                    capture_output=True,
                    text=True
                )
                
                if result3.returncode == 0:
                    print("✅ Archivo restaurado desde origin/main")
                else:
                    print("❌ Error al restaurar desde origin/main")
                    print(f"   {result3.stderr}")
        else:
            print(f"❌ Error al restaurar desde Git: {result.stderr}")
            print("   Intentando limpieza manual...")
            
            # Limpieza manual
            lines = content.split('\n')
            new_lines = []
            removed = 0
            
            for line in lines:
                if line.strip().startswith('<<<<<<<') or \
                   line.strip() == '=======' or \
                   line.strip().startswith('>>>>>>>'):
                    removed += 1
                    continue
                new_lines.append(line)
            
            if removed > 0:
                new_content = '\n'.join(new_lines)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ Eliminadas {removed} líneas con marcadores de conflicto")
            else:
                print("❌ No se pudieron eliminar los marcadores")
                sys.exit(1)
    except Exception as e:
        print(f"❌ Error al ejecutar Git: {e}")
        sys.exit(1)
else:
    print("\n✅ No se encontraron marcadores de conflicto")

# Verificar sintaxis Python
print("\n🔍 Verificando sintaxis Python...")
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    compile(code, file_path, 'exec')
    print("✅ Sintaxis Python válida")
except SyntaxError as e:
    print(f"❌ Error de sintaxis: {e}")
    print(f"   Línea {e.lineno}: {e.text}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error al compilar: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ PROCESO COMPLETADO")
print("=" * 60)
print("\n💡 Recuerda reiniciar el servidor WSGI:")
print("   touch /var/www/www_egarage_cl_wsgi.py")
print()

