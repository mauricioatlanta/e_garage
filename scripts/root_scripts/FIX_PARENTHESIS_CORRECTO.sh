#!/bin/bash
# Script corregido para arreglar el error de paréntesis en la función enviar_documento_whatsapp
# Ejecutar en el servidor

cd /home/atlantareciclajes/apps/egarage/current || exit 1

echo "📋 Creando backup..."
cp taller/documentos/views.py taller/documentos/views.py.backup_paren2_$(date +%Y%m%d_%H%M%S)

echo "🔧 Corrigiendo error de paréntesis en enviar_documento_whatsapp..."

python3 << 'PYEOF'
import sys

file_path = "taller/documentos/views.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar la función enviar_documento_whatsapp específicamente
func_start = None
for i, line in enumerate(lines):
    if 'def enviar_documento_whatsapp' in line:
        func_start = i
        break

if func_start is None:
    print("❌ No se encontró la función enviar_documento_whatsapp")
    sys.exit(1)

print(f"📍 Función encontrada en línea {func_start + 1}")

# Buscar el return JsonResponse DENTRO de esta función (después de la línea de cierre del f-string)
return_idx = None
target_string = '¡Gracias por confiar en nuestros servicios!"""'

# Primero encontrar la línea con el cierre del f-string
fstring_close_idx = None
for i in range(func_start, min(func_start + 100, len(lines))):
    if target_string in lines[i]:
        fstring_close_idx = i
        break

if fstring_close_idx is None:
    print("❌ No se encontró la línea de cierre del f-string")
    sys.exit(1)

print(f"📍 Cierre del f-string en línea {fstring_close_idx + 1}")

# Ahora buscar el return JsonResponse después del cierre del f-string
for i in range(fstring_close_idx + 1, min(func_start + 100, len(lines))):
    if 'return JsonResponse(' in lines[i]:
        return_idx = i
        break

if return_idx is None:
    print("❌ No se encontró return JsonResponse después del f-string")
    sys.exit(1)

print(f"📍 return JsonResponse encontrado en línea {return_idx + 1}")

# Leer el área problemática para diagnóstico
print("\n📄 Área problemática actual:")
for i in range(return_idx, min(return_idx + 10, len(lines))):
    marker = ">>>" if i == return_idx else "   "
    print(f"{marker} {i+1:4d}: {repr(lines[i][:60])}")

# Encontrar dónde debería terminar el bloque
# El bloque debe tener esta estructura:
# return JsonResponse(
#     {
#         "success": True,
#         "url_whatsapp": url_whatsapp,
#         "telefono": telefono,
#         "mensaje": mensaje,
#     }
# )

# Buscar el final del bloque actual contando paréntesis y llaves
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
    elif i == return_idx + 15:  # Límite de seguridad
        # Si no encontramos el final, asumir que termina aquí
        block_end = i
        break

print(f"📍 Fin del bloque actual en línea {block_end + 1}")

# Crear el bloque correcto con indentación de 4 espacios
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

print("\n📄 Bloque corregido:")
for i, line in enumerate(correct_block, return_idx + 1):
    print(f"   {i:4d}: {repr(line[:60])}")

# Verificar sintaxis
try:
    code = ''.join(new_lines)
    compile(code, file_path, 'exec')
    print("\n✅ Sintaxis válida")
except SyntaxError as e:
    print(f"\n❌ Error de sintaxis en línea {e.lineno}: {e.msg}")
    if e.lineno <= len(new_lines):
        print(f"   Línea problemática: {repr(new_lines[e.lineno-1][:80])}")
    
    # Mostrar más contexto
    print("\n📄 Contexto alrededor del error:")
    start = max(0, e.lineno - 5)
    end = min(len(new_lines), e.lineno + 5)
    for i in range(start, end):
        marker = ">>>" if i == e.lineno - 1 else "   "
        print(f"{marker} {i+1:4d}: {repr(new_lines[i][:60])}")
    
    sys.exit(1)

# Escribir archivo corregido
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Archivo corregido exitosamente")
PYEOF

echo ""
echo "🔍 Verificando sintaxis final..."
if python3 -m py_compile taller/documentos/views.py; then
    echo "✅ Verificación de sintaxis exitosa"
    touch /var/www/www_egarage_cl_wsgi.py
    echo "✅ Servidor reiniciado"
else
    echo "❌ Aún hay errores de sintaxis"
    exit 1
fi

