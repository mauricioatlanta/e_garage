#!/bin/bash
# Script para corregir el error "unmatched ')'" en views.py
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

echo "📋 Creando backup..."
cp taller/documentos/views.py taller/documentos/views.py.backup_paren_$(date +%Y%m%d_%H%M%S)

echo "🔧 Corrigiendo error de paréntesis..."

python3 << 'PYEOF'
import sys

file_path = "taller/documentos/views.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar la línea con return JsonResponse
return_idx = None
for i, line in enumerate(lines):
    if 'return JsonResponse(' in line:
        return_idx = i
        break

if return_idx is None:
    print("❌ No se encontró return JsonResponse")
    sys.exit(1)

print(f"📍 return JsonResponse encontrado en línea {return_idx + 1}")

# Buscar dónde termina el bloque (siguiente línea que no sea parte del JsonResponse)
# El bloque debe tener esta estructura:
# return JsonResponse(
#     {
#         "success": True,
#         "url_whatsapp": url_whatsapp,
#         "telefono": telefono,
#         "mensaje": mensaje,
#     }
# )

# Encontrar el final del bloque actual
block_end = return_idx + 1
paren_count = 1  # Ya tenemos el '(' del JsonResponse(
brace_count = 0

for i in range(return_idx + 1, min(return_idx + 20, len(lines))):
    line = lines[i]
    paren_count += line.count('(') - line.count(')')
    brace_count += line.count('{') - line.count('}')
    
    if paren_count == 0 and brace_count == 0:
        block_end = i
        break

print(f"📍 Fin del bloque actual en línea {block_end + 1}")

# Crear el bloque correcto con indentación adecuada (4 espacios)
correct_block = [
    '    return JsonResponse(\n',
    '        {\n',
    '            "success": True,\n',
    '            "url_whatsapp": url_whatsapp,\n',
    '            "telefono": telefono,\n',
    '            "mensaje": mensaje,\n',
    '        }\n',
    '    )\n'
]

# Reemplazar el bloque
new_lines = lines[:return_idx] + correct_block + lines[block_end + 1:]

# Verificar sintaxis
try:
    code = ''.join(new_lines)
    compile(code, file_path, 'exec')
    print("✅ Sintaxis válida")
except SyntaxError as e:
    print(f"❌ Error de sintaxis en línea {e.lineno}: {e.msg}")
    print(f"   Contenido: {repr(lines[e.lineno-1][:60])}")
    sys.exit(1)

# Escribir archivo corregido
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Archivo corregido exitosamente")
PYEOF

echo ""
echo "✅ Proceso completado"
echo "💡 Verifica con: python3 -m py_compile taller/documentos/views.py"

