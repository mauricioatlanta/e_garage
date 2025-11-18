#!/usr/bin/env python3
"""
Script preciso para corregir el f-string en views.py
Ejecutar en el servidor: python3 CORREGIR_FSTRING_PRECISO.py
"""
import os
import re

file_path = "taller/documentos/views.py"

if not os.path.exists(file_path):
    print(f"❌ Error: {file_path} no encontrado")
    print(f"   cd /home/atlantareciclajes/apps/egarage/current")
    exit(1)

print(f"📄 Procesando {file_path}...")

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Crear backup
backup_path = f"{file_path}.backup"
with open(backup_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print(f"📦 Backup creado: {backup_path}")

# Buscar la línea problemática
# Buscar línea que tenga: f"https://wa.me/...?text={mensaje.replace(...).replace('\n', ...)}"
# Pero NO debe estar dentro de un f-string multilinea (entre """ o ''')
new_lines = []
in_multiline_string = False
string_char = None
found_problem = False

for i, line in enumerate(lines, start=1):
    original_line = line
    
    # Detectar inicio/fin de strings multilinea
    if '"""' in line or "'''" in line:
        # Contar cuántas veces aparece
        count = line.count('"""') + line.count("'''")
        if count % 2 == 1:  # Si es impar, cambia el estado
            in_multiline_string = not in_multiline_string
            if in_multiline_string:
                # Determinar qué carácter de cita se está usando
                if '"""' in line:
                    string_char = '"""'
                elif "'''" in line:
                    string_char = "'''"
    
    # Si estamos dentro de un string multilinea, mantener la línea como está
    if in_multiline_string:
        new_lines.append(line)
        continue
    
    # Buscar línea problemática: f-string con wa.me y mensaje.replace que tenga \n
    if ('wa.me' in line and 'f"' in line and 'mensaje' in line and 
        'replace' in line and ('\\n' in line or "'\\n'" in line or '"\\n"' in line)):
        
        print(f"⚠️  Línea {i} problemática encontrada:")
        print(f"   {line.strip()[:80]}")
        
        # Verificar el contexto: debe estar después de definir mensaje y antes de return
        # Buscar si hay un mensaje definido antes (en las 10 líneas anteriores)
        context_ok = False
        for j in range(max(0, i-15), i-1):
            if j < len(lines) and ('mensaje = ' in lines[j] or 'mensaje=' in lines[j]):
                context_ok = True
                break
        
        if not context_ok:
            print(f"   ⚠️  No se encontró contexto apropiado, revisando...")
            # Mostrar contexto
            for j in range(max(0, i-5), min(len(lines), i+3)):
                marker = ">>> " if j == i-1 else "    "
                print(f"{marker}{j+1:4d}: {lines[j].rstrip()}")
        
        # Obtener indentación
        indent = len(line) - len(line.lstrip())
        indent_str = ' ' * indent
        
        # Reemplazar la línea problemática
        # Buscar el patrón exacto para reemplazarlo
        # Patrón: f"https://wa.me/{...}?text={mensaje.replace(...).replace('\n', ...)}"
        pattern = r'f"https://wa\.me/\{[^}]+\}\?text=\{mensaje\.replace\([^)]+\)\.replace\([^)]*\\n[^)]+\)\}"'
        
        if re.search(pattern, line):
            # Reemplazar con código corregido
            new_lines.append(indent_str + '# Crear URL de WhatsApp\n')
            new_lines.append(indent_str + '# Nota: No se pueden usar backslashes directamente en expresiones f-string\n')
            new_lines.append(indent_str + 'mensaje_encoded = mensaje.replace(" ", "%20").replace("\\n", "%0A")\n')
            
            # Extraer la variable telefono del patrón original
            # Buscar {telefono} o {variable} en el f-string original
            telefono_match = re.search(r'\{([^}]+)\}', line)
            if telefono_match:
                telefono_var = telefono_match.group(1)
                new_lines.append(indent_str + f'url_whatsapp = f"https://wa.me/{{{telefono_var}}}?text={{mensaje_encoded}}"\\n')
            else:
                # Si no se encuentra, usar telefono por defecto
                new_lines.append(indent_str + 'url_whatsapp = f"https://wa.me/{telefono}?text={mensaje_encoded}"\\n')
            
            found_problem = True
            print(f"✅ Línea {i} reemplazada con código corregido")
        else:
            # Si el patrón no coincide exactamente, intentar reemplazo más simple
            # Solo reemplazar la parte problemática
            if 'mensaje.replace' in line and '\\n' in line:
                # Extraer todo antes del ?text= y después
                parts = line.split('?text=')
                if len(parts) == 2:
                    before = parts[0]
                    after = parts[1]
                    
                    # Si after contiene el problema
                    if 'mensaje.replace' in after and '\\n' in after:
                        new_lines.append(indent_str + '# Crear URL de WhatsApp\\n')
                        new_lines.append(indent_str + '# Nota: No se pueden usar backslashes directamente en expresiones f-string\\n')
                        new_lines.append(indent_str + 'mensaje_encoded = mensaje.replace(" ", "%20").replace("\\n", "%0A")\\n')
                        new_lines.append(indent_str + before + '?text={mensaje_encoded}"\\n')
                        found_problem = True
                        print(f"✅ Línea {i} corregida (método simple)")
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
    else:
        new_lines.append(line)

if not found_problem:
    print("⚠️  No se encontró el f-string problemático")
    print("   Buscando líneas relacionadas...")
    for i, line in enumerate(lines, start=1):
        if 'wa.me' in line:
            print(f"   Línea {i}: {line.strip()[:100]}")

# Escribir el archivo corregido
if found_problem:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    # Verificar sintaxis
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        compile(content, file_path, 'exec')
        print("✅ Sintaxis Python válida")
    except SyntaxError as e:
        print(f"❌ Error de sintaxis: {e}")
        print(f"   Línea {e.lineno}: {e.text}")
        print("🔄 Restaurando desde backup...")
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_content = f.read()
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(backup_content)
        exit(1)

print("\\n✅ Proceso completado")
print("\\n💡 Reinicia el servidor WSGI:")
print("   touch /var/www/www_egarage_cl_wsgi.py")

