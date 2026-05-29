#!/bin/bash
# Script final para corregir taller/documentos/views.py en el servidor

RELEASE_DIR="/home/atlantareciclajes/apps/egarage/releases/2025-11-17_1615_eg"

cd "$RELEASE_DIR" || exit 1

echo "🔧 Corrigiendo taller/documentos/views.py..."

# Opción 1: Obtener la versión correcta desde origin/main
echo "📥 Obteniendo versión correcta desde origin/main..."
if git show origin/main:taller/documentos/views.py > /tmp/views_correcto.py 2>/dev/null; then
    cp /tmp/views_correcto.py taller/documentos/views.py
    echo "✅ Archivo reemplazado con versión de origin/main"
    
    # Verificar sintaxis
    if python3 -m py_compile taller/documentos/views.py 2>/dev/null; then
        echo "✅ Sintaxis verificada correctamente"
    else
        echo "❌ Error: La versión de origin/main también tiene problemas"
        exit 1
    fi
else
    echo "⚠️  No se pudo obtener desde origin/main. Corrigiendo manualmente..."
    
    # Opción 2: Corregir manualmente usando Python
    python3 << 'PYEOF'
file_path = 'taller/documentos/views.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar la línea problemática alrededor de 1216
fixed = False
for i in range(max(0, 1210), min(len(lines), 1225)):
    line = lines[i]
    
    # Buscar líneas con url_whatsapp y mensaje.replace
    if 'url_whatsapp' in line or ('mensaje' in line and 'replace' in line and i >= 1214):
        # Verificar si la línea está rota o tiene el problema del backslash
        if '\\n' in line and 'f"' in line and 'replace' in line:
            # Encontrar el inicio del bloque (buscar comentario o url_whatsapp)
            start = i
            while start > 0 and not ('# Crear URL' in lines[start] or 'url_whatsapp' in lines[start]):
                start -= 1
            
            # Encontrar el final del bloque
            end = i
            while end < len(lines) and ')' not in lines[end] and end < i + 5:
                end += 1
            
            # Reemplazar con la versión correcta
            indent = len(lines[start]) - len(lines[start].lstrip()) if start < len(lines) else 4
            new_lines = [
                ' ' * indent + "# Crear URL de WhatsApp\n",
                ' ' * indent + "# Nota: No se pueden usar backslashes directamente en expresiones f-string\n",
                ' ' * indent + "mensaje_encoded = mensaje.replace(' ', '%20').replace('\\n', '%0A')\n",
                ' ' * indent + 'url_whatsapp = f"https://wa.me/{telefono}?text={mensaje_encoded}"\n'
            ]
            
            # Asegurarse de que end incluya la línea con el paréntesis
            if end < len(lines) and ')' in lines[end]:
                end += 1
            
            lines[start:end+1] = new_lines
            fixed = True
            print(f"✅ Líneas {start+1}-{end+1} reemplazadas")
            break
        
        # También verificar si hay una cadena sin terminar
        if "'" in line and line.count("'") % 2 != 0:
            # La cadena está rota, necesitamos arreglarla
            print(f"⚠️  Cadena rota detectada en línea {i+1}")
            # Buscar la siguiente línea que complete la cadena
            j = i + 1
            while j < len(lines) and lines[j].count("'") % 2 == 0:
                j += 1
            # Reemplazar todo el bloque
            indent = len(lines[i]) - len(lines[i].lstrip())
            new_lines = [
                ' ' * indent + "# Crear URL de WhatsApp\n",
                ' ' * indent + "# Nota: No se pueden usar backslashes directamente en expresiones f-string\n",
                ' ' * indent + "mensaje_encoded = mensaje.replace(' ', '%20').replace('\\n', '%0A')\n",
                ' ' * indent + 'url_whatsapp = f"https://wa.me/{telefono}?text={mensaje_encoded}"\n'
            ]
            lines[i:j+1] = new_lines
            fixed = True
            print(f"✅ Líneas {i+1}-{j+1} reemplazadas (cadena rota)")
            break

if fixed:
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("✅ Archivo corregido")
    
    # Verificar sintaxis
    import py_compile
    try:
        py_compile.compile(file_path, doraise=True)
        print("✅ Sintaxis verificada correctamente")
    except py_compile.PyCompileError as e:
        print(f"❌ Error de sintaxis: {e}")
        exit(1)
else:
    print("⚠️  No se encontró el problema o ya está corregido")
PYEOF
fi

echo ""
echo "🔄 Reiniciando servidor..."
touch /var/www/www_atlantareciclajes_digitalocean_com_wsgi.py
echo "✅ Servidor reiniciado"



