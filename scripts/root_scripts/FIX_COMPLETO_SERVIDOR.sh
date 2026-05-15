#!/bin/bash
# Script completo para corregir el área problemática completa
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

echo "📋 Creando backup..."
cp taller/documentos/views.py taller/documentos/views.py.backup_completo_$(date +%Y%m%d_%H%M%S)

echo "🔧 Corrigiendo área problemática completa..."

python3 << 'PYEOF'
import sys

file_path = "taller/documentos/views.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar la función enviar_documento_whatsapp
func_start = None
for i, line in enumerate(lines):
    if 'def enviar_documento_whatsapp' in line:
        func_start = i
        break

if func_start is None:
    print("❌ No se encontró la función")
    sys.exit(1)

print(f"📍 Función en línea {func_start + 1}")

# Buscar el cierre del f-string
fstring_close_idx = None
for i in range(func_start, min(func_start + 100, len(lines))):
    if '¡Gracias por confiar en nuestros servicios!"""' in lines[i]:
        fstring_close_idx = i
        break

if fstring_close_idx is None:
    print("❌ No se encontró el cierre del f-string")
    sys.exit(1)

print(f"📍 Cierre del f-string en línea {fstring_close_idx + 1}")

# Mostrar el área problemática actual
print("\n📄 Área problemática ACTUAL (líneas 1212-1235):")
for i in range(fstring_close_idx, min(fstring_close_idx + 25, len(lines))):
    print(f"{i+1:4d}: {repr(lines[i][:70])}")

# Buscar dónde termina la función (siguiente 'def' o fin de archivo)
func_end = len(lines)
for i in range(func_start + 1, len(lines)):
    stripped = lines[i].strip()
    if stripped.startswith('def ') and not stripped.startswith('def ' + ' '):
        func_end = i
        break

print(f"\n📍 Fin de función en línea {func_end + 1}")

# Reconstruir el bloque completo desde el cierre del f-string hasta antes del return
# El bloque correcto debe ser:
# (línea con cierre del f-string)
# (línea vacía)
#     # Crear URL de WhatsApp
#     # Nota: No se pueden usar backslashes directamente en expresiones f-string
#     mensaje_encoded = mensaje.replace(" ", "%20").replace("\n", "%0A")
#     url_whatsapp = f"https://wa.me/{telefono}?text={mensaje_encoded}"
# (línea vacía)
#     return JsonResponse(
#         {
#             "success": True,
#             "url_whatsapp": url_whatsapp,
#             "telefono": telefono,
#             "mensaje": mensaje,
#         }
#     )

# Buscar el inicio del bloque que debemos reemplazar
# Debe empezar después del cierre del f-string
replace_start = fstring_close_idx + 1

# Buscar el return JsonResponse para saber dónde termina lo que debemos reemplazar
return_idx = None
for i in range(fstring_close_idx + 1, func_end):
    if 'return JsonResponse(' in lines[i]:
        return_idx = i
        break

if return_idx is None:
    print("❌ No se encontró return JsonResponse")
    sys.exit(1)

print(f"📍 return JsonResponse en línea {return_idx + 1}")

# Encontrar dónde termina el bloque JsonResponse actual
block_end = return_idx + 1
paren_count = 1
brace_count = 0

for i in range(return_idx + 1, min(return_idx + 20, func_end)):
    line = lines[i]
    paren_count += line.count('(') - line.count(')')
    brace_count += line.count('{') - line.count('}')
    if paren_count == 0 and brace_count == 0:
        block_end = i
        break
    elif i == return_idx + 15:
        block_end = i
        break

print(f"📍 Fin del bloque JsonResponse en línea {block_end + 1}")

# Crear el bloque correcto completo
# Desde después del cierre del f-string hasta el final del return JsonResponse
correct_block = [
    '\n',  # Línea vacía después del cierre del f-string
    '    # Crear URL de WhatsApp\n',
    '    # Nota: No se pueden usar backslashes directamente en expresiones f-string\n',
    '    mensaje_encoded = mensaje.replace(" ", "%20").replace("\\n", "%0A")\n',
    '    url_whatsapp = f"https://wa.me/{telefono}?text={mensaje_encoded}"\n',
    '\n',  # Línea vacía
    '    return JsonResponse(\n',
    '        {\n',
    '            "success": True,\n',
    '            "url_whatsapp": url_whatsapp,\n',
    '            "telefono": telefono,\n',
    '            "mensaje": mensaje,\n',
    '        }\n',
    '    )\n'
]

# Reemplazar desde después del cierre del f-string hasta el final del bloque JsonResponse
new_lines = lines[:replace_start] + correct_block + lines[block_end + 1:]

print("\n📄 Bloque CORREGIDO:")
for i, line in enumerate(correct_block, replace_start + 1):
    print(f"{i:4d}: {repr(line[:70])}")

# Verificar sintaxis
try:
    code = ''.join(new_lines)
    compile(code, file_path, 'exec')
    print("\n✅ Sintaxis válida")
except SyntaxError as e:
    print(f"\n❌ Error en línea {e.lineno}: {e.msg}")
    if e.lineno <= len(new_lines):
        print(f"   Línea problemática: {repr(new_lines[e.lineno-1][:70])}")
    
    # Mostrar más contexto
    print("\n📄 Contexto alrededor del error:")
    start = max(0, e.lineno - 5)
    end = min(len(new_lines), e.lineno + 5)
    for i in range(start, end):
        marker = ">>>" if i == e.lineno - 1 else "   "
        print(f"{marker} {i+1:4d}: {repr(new_lines[i][:70])}")
    
    sys.exit(1)

# Escribir archivo corregido
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Archivo corregido exitosamente")
PYEOF

echo ""
echo "🔍 Verificando sintaxis..."
if python3 -m py_compile taller/documentos/views.py; then
    echo "✅ Sintaxis correcta"
    touch /var/www/www_egarage_cl_wsgi.py
    echo "✅ Servidor reiniciado"
else
    echo "❌ Aún hay errores"
    exit 1
fi

