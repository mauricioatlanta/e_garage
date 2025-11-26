#!/usr/bin/env python3
"""
Script definitivo para corregir el f-string en views.py
Busca dónde TERMINA el f-string multilinea y reemplaza la línea problemática DESPUÉS de él
"""
import os
import re

file_path = "taller/documentos/views.py"

if not os.path.exists(file_path):
    print(f"❌ Error: {file_path} no encontrado")
    exit(1)

print(f"📄 Procesando {file_path}...")

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Crear backup
backup_path = f"{file_path}.backup_final"
with open(backup_path, "w", encoding="utf-8") as f:
    f.writelines(lines)
print(f"📦 Backup creado: {backup_path}")

# Encontrar dónde TERMINA el f-string multilinea (buscar la línea con """)
multiline_end_idx = None
for i, line in enumerate(lines):
    # Buscar línea que contenga """ y esté después de definir "mensaje = f"""
    if '"""' in line and i > 1200 and i < 1220:
        # Verificar que la línea anterior tenga "mensaje"
        if i > 0 and ("mensaje" in lines[i - 1] or "mensaje" in "".join(lines[max(0, i - 5) : i])):
            multiline_end_idx = i
            print(f"✅ Fin de f-string multilinea encontrado en línea {i+1}")
            print(f"   {line.strip()}")
            break

if multiline_end_idx is None:
    print("⚠️  No se encontró el fin del f-string multilinea")
    print("   Buscando en un rango más amplio...")
    for i in range(1210, min(len(lines), 1220)):
        print(f"   Línea {i+1}: {lines[i].strip()[:80]}")

# Ahora buscar la línea problemática DESPUÉS del f-string multilinea
# Debe estar después de multiline_end_idx
target_idx = None
start_search = multiline_end_idx + 1 if multiline_end_idx else 1215
end_search = min(len(lines), 1235)

print(f"\n📋 Buscando línea problemática después de línea {start_search}...")

for i in range(start_search, end_search):
    line = lines[i]
    # Buscar línea con wa.me que tenga f-string con mensaje.replace y \n
    if (
        "wa.me" in line
        and 'f"' in line
        and "mensaje" in line
        and ("replace" in line or "\\n" in line or "'\\n'" in line)
    ):
        target_idx = i
        print(f"✅ Línea problemática encontrada en línea {i+1}")
        print(f"   {line.strip()[:100]}")
        break

if target_idx is None:
    print("⚠️  No se encontró la línea problemática")
    print("   Mostrando líneas después del f-string multilinea:")
    for i in range(start_search, end_search):
        print(f"   {i+1:4d}: {lines[i].strip()[:100]}")
    exit(1)

# Verificar contexto: mostrar líneas alrededor
print(f"\n📋 Contexto alrededor de línea {target_idx + 1}:")
for i in range(max(0, target_idx - 2), min(len(lines), target_idx + 5)):
    marker = ">>> " if i == target_idx else "    "
    print(f"{marker}{i+1:4d}: {lines[i].rstrip()}")

# Verificar que NO estamos dentro de un f-string
# Si la línea anterior tiene """, estamos fuera del string (correcto)
# Si no, debemos verificar si estamos dentro
if target_idx > 0:
    prev_lines_text = "".join(lines[max(0, target_idx - 10) : target_idx])
    # Contar """ antes de esta línea
    triple_quotes_before = prev_lines_text.count('"""')
    if triple_quotes_before % 2 == 1:
        print("⚠️  ADVERTENCIA: Parece estar dentro de un string multilinea")
        # Buscar dónde realmente termina
        for i in range(target_idx - 1, max(0, target_idx - 20), -1):
            if '"""' in lines[i]:
                print(f"   String multilinea termina en línea {i+1}")
                target_idx = i + 1  # Insertar después del cierre
                break

# Obtener indentación
problem_line = lines[target_idx]
indent = len(problem_line) - len(problem_line.lstrip())
indent_str = " " * indent

# Extraer variable telefono del f-string original
telefono_match = re.search(r"\{([^}]+)\}", problem_line)
telefono_var = telefono_match.group(1) if telefono_match else "telefono"

print(f"\n✅ Reemplazando línea {target_idx + 1}")
print(f"   Indentación: {indent} espacios")
print(f"   Variable telefono: {telefono_var}")

# Reemplazar la línea problemática
new_lines = (
    lines[:target_idx]
    + [
        indent_str + "# Crear URL de WhatsApp\n",
        indent_str + "# Nota: No se pueden usar backslashes directamente en expresiones f-string\n",
        indent_str + 'mensaje_encoded = mensaje.replace(" ", "%20").replace("\\n", "%0A")\n',
        indent_str
        + f'url_whatsapp = f"https://wa.me/{{{telefono_var}}}?text={{mensaje_encoded}}"\\n',
    ]
    + lines[target_idx + 1 :]
)

# Escribir archivo
with open(file_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("✅ Archivo actualizado")

# Verificar sintaxis
try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    compile(content, file_path, "exec")
    print("✅ Sintaxis Python válida")
except SyntaxError as e:
    print(f"❌ Error de sintaxis: {e}")
    print(f"   Línea {e.lineno}: {e.text}")
    print("🔄 Restaurando desde backup...")
    with open(backup_path, "r", encoding="utf-8") as f:
        backup_content = f.read()
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(backup_content)
    exit(1)

print("\n✅ Proceso completado exitosamente")
print("\n💡 Reinicia el servidor WSGI:")
print("   touch /var/www/www_egarage_cl_wsgi.py")
