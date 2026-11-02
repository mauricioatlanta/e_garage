#!/bin/bash
# Script directo: escribir función completa correcta

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Escribiendo función enviar_documento_whatsapp directamente..."

python3 << 'PYEOF'
file_path = "taller/documentos/views.py"

# Leer archivo
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar inicio de función
func_start = None
for i, line in enumerate(lines):
    if 'def enviar_documento_whatsapp' in line:
        func_start = i
        break

if func_start is None:
    print("❌ No se encontró la función")
    sys.exit(1)

print(f"📍 Función encontrada en línea {func_start + 1}")

# Encontrar fin de función (buscar siguiente def o class al mismo nivel)
func_end = None
func_indent = len(lines[func_start]) - len(lines[func_start].lstrip())

for i in range(func_start + 1, len(lines)):
    line = lines[i]
    if not line.strip():
        continue
    
    current_indent = len(line) - len(line.lstrip())
    stripped = line.lstrip()
    
    # Si encontramos otra función/clase al mismo nivel o menos, es el fin
    if current_indent <= func_indent:
        if stripped.startswith('def ') or stripped.startswith('class '):
            func_end = i
            break

if func_end is None:
    # Buscar el último ')' que cierra el return JsonResponse
    for i in range(func_start + 60, func_start + 80):
        if i < len(lines) and lines[i].strip() == ')':
            func_end = i + 1
            break

if func_end is None:
    func_end = func_start + 75  # Asumir 75 líneas máximo

print(f"📍 Función termina en línea {func_end}")

# Función correcta (con 4 espacios de indentación base)
funcion_correcta_lines = [
    'def enviar_documento_whatsapp(request, documento_id):',
    '    """',
    '    Vista para enviar documento por WhatsApp',
    '    """',
    '    import re',
    '',
    '    from django.http import JsonResponse',
    '',
    '    from taller.models import Documento',
    '',
    '    try:',
    '        documento = Documento.objects.get(id=documento_id, empresa=request.user.empresa)',
    '    except Documento.DoesNotExist:',
    '        return JsonResponse({"success": False, "error": "Documento no encontrado"}, status=404)',
    '',
    '    # Verificar que el cliente tenga teléfono',
    '    if not documento.cliente.telefono:',
    '        return JsonResponse(',
    '            {',
    '                "success": False,',
    '                "error": "El cliente no tiene número de teléfono registrado",',
    '            }',
    '        )',
    '',
    '    # Limpiar y validar número de teléfono',
    '    telefono = (',
    '        documento.cliente.telefono.replace("+", "")',
    '        .replace(" ", "")',
    '        .replace("-", "")',
    '        .replace("(", "")',
    '        .replace(")", "")',
    '    )',
    '',
    '    # Validar formato chileno',
    '    if not re.match(r"^(\\+56|56)?[2-9]\\d{8}$", telefono):',
    '        return JsonResponse(',
    '            {',
    '                "success": False,',
    '                "error": "Número de teléfono inválido. Debe ser un número chileno válido",',
    '            }',
    '        )',
    '',
    '    # Formatear número para WhatsApp',
    '    if not telefono.startswith("56"):',
    '        telefono = "56" + telefono',
    '',
    '    # Crear mensaje personalizado',
    '    mensaje = f"""Hola {documento.cliente.nombre},',
    '',
    'Adjunto encontrará el documento del taller.',
    '',
    '📄 {documento.get_tipo_display()} #{documento.numero_documento}',
    '🏢 {documento.empresa.nombre_taller}',
    '📅 Fecha: {documento.fecha_emision.strftime(\'%d/%m/%Y\')}',
    '💰 Total: ${documento.total_general():,.0f}',
    '',
    'Para ver el documento completo, visite:',
    '{request.build_absolute_uri(f\'/cl/documentos/{documento.id}/\')}',
    '',
    '¡Gracias por confiar en nuestros servicios!"""',
    '',
    '    # Crear URL de WhatsApp',
    '    # Nota: No se pueden usar backslashes directamente en expresiones f-string',
    '    mensaje_encoded = mensaje.replace(" ", "%20").replace("\\n", "%0A")',
    '    url_whatsapp = f"https://wa.me/{telefono}?text={mensaje_encoded}"',
    '',
    '    return JsonResponse(',
    '        {',
    '            "success": True,',
    '            "url_whatsapp": url_whatsapp,',
    '            "telefono": telefono,',
    '            "mensaje": mensaje,',
    '        }',
    '    )',
    ''
]

# Reemplazar
new_lines = lines[:func_start] + [line + '\n' for line in funcion_correcta_lines] + lines[func_end:]

# Escribir archivo
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Función escrita correctamente")

# Verificar sintaxis
import ast
try:
    content = ''.join(new_lines)
    ast.parse(content)
    print("✅ Sintaxis verificada correctamente")
except SyntaxError as e:
    print(f"❌ Error de sintaxis: {e}")
    print(f"   Línea {e.lineno}: {e.text}")
    sys.exit(1)

print("✅ Archivo guardado")
PYEOF

echo ""
echo "✅✅✅ Función escrita correctamente ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



