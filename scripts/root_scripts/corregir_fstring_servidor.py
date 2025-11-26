#!/usr/bin/env python3
"""
Script para corregir el f-string con backslash en taller/documentos/views.py
Ejecutar en el servidor: python3 corregir_fstring_servidor.py
"""
import os
import re

file_path = "taller/documentos/views.py"

if not os.path.exists(file_path):
    print(f"❌ Error: {file_path} no encontrado")
    print(f"   Cambia al directorio del proyecto primero:")
    print(f"   cd /home/atlantareciclajes/apps/egarage/current")
    exit(1)

print(f"📄 Procesando {file_path}...")

# Leer el archivo
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Crear backup
backup_path = f"{file_path}.backup"
with open(backup_path, "w", encoding="utf-8") as f:
    f.write(content)
print(f"📦 Backup creado: {backup_path}")

# Buscar y corregir el f-string problemático
# Patrón 1: f"https://wa.me/{telefono}?text={mensaje.replace(' ', '%20').replace('\n', '%0A')}"
pattern1 = (
    r'f"https://wa\.me/\{telefono\}\?text=\{mensaje\.replace\([^)]+\)\.replace\([^)]*\\n[^)]+\)\}"'
)

if re.search(pattern1, content):
    print("⚠️  Encontrado f-string problemático (patrón 1)")

    # Reemplazar con la versión corregida
    replacement = '''    # Crear URL de WhatsApp
    # Nota: No se pueden usar backslashes directamente en expresiones f-string
    mensaje_encoded = mensaje.replace(" ", "%20").replace("\\n", "%0A")
    url_whatsapp = f"https://wa.me/{telefono}?text={mensaje_encoded}"'''

    # Buscar la línea completa y reemplazarla
    lines = content.split("\n")
    new_lines = []
    i = 0
    found = False

    while i < len(lines):
        line = lines[i]

        # Buscar la línea con el f-string problemático
        if "wa.me" in line and "mensaje.replace" in line and "\\n" in line:
            print(f"   Línea {i+1}: {line[:80]}...")

            # Encontrar dónde comienza la función/view
            start_idx = i
            while (
                start_idx > 0
                and not lines[start_idx].strip().startswith("def ")
                and not lines[start_idx].strip().startswith("@")
            ):
                start_idx -= 1

            # Buscar el comentario previo o la línea anterior
            # Insertar el código corregido
            indent = len(line) - len(line.lstrip())

            # Eliminar la línea problemática
            # Y reemplazar con el código corregido
            new_lines.append(" " * indent + "# Crear URL de WhatsApp")
            new_lines.append(
                " " * indent
                + "# Nota: No se pueden usar backslashes directamente en expresiones f-string"
            )
            new_lines.append(
                " " * indent + 'mensaje_encoded = mensaje.replace(" ", "%20").replace("\\n", "%0A")'
            )
            new_lines.append(
                " " * indent + 'url_whatsapp = f"https://wa.me/{telefono}?text={mensaje_encoded}"'
            )
            found = True
        else:
            new_lines.append(line)
        i += 1

    if found:
        content = "\n".join(new_lines)
        print("✅ F-string corregido")
    else:
        # Intentar con regex directo
        old_pattern = r'(\s+)(f"https://wa\.me/\{telefono\}\?text=\{mensaje\.replace\([^)]+\)\.replace\([^)]*\\n[^)]+\)\}")'
        replacement = r'\1# Crear URL de WhatsApp\n\1# Nota: No se pueden usar backslashes directamente en expresiones f-string\n\1mensaje_encoded = mensaje.replace(" ", "%20").replace("\\n", "%0A")\n\1url_whatsapp = f"https://wa.me/{telefono}?text={mensaje_encoded}"'

        new_content = re.sub(old_pattern, replacement, content)
        if new_content != content:
            content = new_content
            print("✅ F-string corregido (método regex)")
        else:
            print("⚠️  No se encontró el patrón exacto, intentando búsqueda más amplia...")
            # Buscar cualquier línea con wa.me y replace con \n
            for i, line in enumerate(content.split("\n")):
                if "wa.me" in line and "mensaje" in line and ("replace" in line or "\\n" in line):
                    print(f"   Línea {i+1} potencial: {line[:100]}")
else:
    print("ℹ️  No se encontró el patrón del f-string problemático")
    print("   Verificando si ya está corregido...")

    if "mensaje_encoded" in content:
        print("✅ El archivo ya parece estar corregido (contiene mensaje_encoded)")
    else:
        # Buscar manualmente
        lines = content.split("\n")
        for i, line in enumerate(lines[1220:1240], start=1221):
            if "wa.me" in line:
                print(f"   Línea {i}: {line}")

# Verificar sintaxis antes de escribir
try:
    compile(content, file_path, "exec")
except SyntaxError as e:
    print(f"❌ Error de sintaxis: {e}")
    print(f"   Línea {e.lineno}: {e.text}")
    print("🔄 Restaurando desde backup...")
    with open(backup_path, "r", encoding="utf-8") as f:
        content = f.read()

# Escribir el archivo corregido
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

# Verificar sintaxis final
try:
    compile(content, file_path, "exec")
    print("✅ Sintaxis Python válida")
except SyntaxError as e:
    print(f"❌ Error de sintaxis: {e}")
    print("🔄 Restaurando desde backup...")
    with open(backup_path, "r", encoding="utf-8") as f:
        backup_content = f.read()
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(backup_content)
    exit(1)

print("\n✅ Proceso completado")
print("\n💡 Recuerda reiniciar el servidor WSGI:")
print("   touch /var/www/www_egarage_cl_wsgi.py")
