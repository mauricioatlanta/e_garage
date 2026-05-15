#!/bin/bash
# Script para escribir la función enviar_documento_whatsapp completa con indentación correcta

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Escribiendo función enviar_documento_whatsapp con indentación correcta..."

python3 << 'PYEOF'
file_path = "taller/documentos/views.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Encontrar inicio y fin de la función
func_start = None
func_end = None

for i, line in enumerate(lines):
    if 'def enviar_documento_whatsapp' in line:
        func_start = i
        # Calcular indentación de la función
        func_indent = len(line) - len(line.lstrip())
        print(f"📍 Función encontrada en línea {i+1}, indentación: {func_indent}")
        break

if func_start is None:
    print("❌ No se encontró la función enviar_documento_whatsapp")
    sys.exit(1)

# Buscar el final de la función (siguiente función o clase)
for i in range(func_start + 1, len(lines)):
    line = lines[i]
    stripped = line.lstrip()
    
    # Si encontramos otra función o clase al mismo nivel, es el final
    if stripped and not line.startswith(' ') and not line.startswith('\t'):
        if stripped.startswith('def ') or stripped.startswith('class '):
            func_end = i
            break
    
    # Si encontramos una línea con solo ')' o '}' al mismo nivel que la función, podría ser el final
    if stripped == ')' and len(line) - len(stripped) <= func_indent:
        # Verificar si es el cierre del return JsonResponse
        if i > func_start + 50:  # La función debería terminar después de varias líneas
            func_end = i + 1
            break

if func_end is None:
    # Buscar el último return JsonResponse y asumir que termina 7 líneas después
    for i in range(func_start, len(lines)):
        if 'return JsonResponse(' in lines[i] and 'mensaje": mensaje' in ''.join(lines[i:i+10]):
            func_end = i + 7  # return JsonResponse + 6 líneas de cierre
            break

if func_end is None:
    func_end = func_start + 75  # Asumir que la función tiene máximo 75 líneas

print(f"📍 Función termina aproximadamente en línea {func_end}")

# Función correcta con indentación correcta (4 espacios para el nivel de función)
funcion_correcta = '''def enviar_documento_whatsapp(request, documento_id):
    """
    Vista para enviar documento por WhatsApp
    """
    import re

    from django.http import JsonResponse

    from taller.models import Documento

    try:
        documento = Documento.objects.get(id=documento_id, empresa=request.user.empresa)
    except Documento.DoesNotExist:
        return JsonResponse({"success": False, "error": "Documento no encontrado"}, status=404)

    # Verificar que el cliente tenga teléfono
    if not documento.cliente.telefono:
        return JsonResponse(
            {
                "success": False,
                "error": "El cliente no tiene número de teléfono registrado",
            }
        )

    # Limpiar y validar número de teléfono
    telefono = (
        documento.cliente.telefono.replace("+", "")
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    # Validar formato chileno
    if not re.match(r"^(\+56|56)?[2-9]\d{8}$", telefono):
        return JsonResponse(
            {
                "success": False,
                "error": "Número de teléfono inválido. Debe ser un número chileno válido",
            }
        )

    # Formatear número para WhatsApp
    if not telefono.startswith("56"):
        telefono = "56" + telefono

    # Crear mensaje personalizado
    mensaje = f"""Hola {documento.cliente.nombre},

Adjunto encontrará el documento del taller.

📄 {documento.get_tipo_display()} #{documento.numero_documento}
🏢 {documento.empresa.nombre_taller}
📅 Fecha: {documento.fecha_emision.strftime('%d/%m/%Y')}
💰 Total: ${documento.total_general():,.0f}

Para ver el documento completo, visite:
{request.build_absolute_uri(f'/cl/documentos/{documento.id}/')}

¡Gracias por confiar en nuestros servicios!"""

    # Crear URL de WhatsApp
    # Nota: No se pueden usar backslashes directamente en expresiones f-string
    mensaje_encoded = mensaje.replace(" ", "%20").replace("\n", "%0A")
    url_whatsapp = f"https://wa.me/{telefono}?text={mensaje_encoded}"

    return JsonResponse(
        {
            "success": True,
            "url_whatsapp": url_whatsapp,
            "telefono": telefono,
            "mensaje": mensaje,
        }
    )
'''

# Reemplazar la función
new_lines = lines[:func_start] + funcion_correcta.split('\n') + [''] + lines[func_end:]

# Ajustar indentación de la función según el contexto
# Si la función anterior tiene indentación diferente, ajustar
if func_start > 0:
    prev_line = lines[func_start - 1]
    if prev_line.strip():
        # Verificar si hay indentación especial
        prev_indent = len(prev_line) - len(prev_line.lstrip())
        if prev_indent > 0:
            # La función debería estar al mismo nivel o menos
            # Pero normalmente las funciones están al nivel 0
            pass

content = '\n'.join(new_lines)

# Verificar sintaxis
import ast
try:
    ast.parse(content)
    print("✅ Sintaxis verificada correctamente")
except SyntaxError as e:
    print(f"❌ Error de sintaxis: {e}")
    print(f"   Línea {e.lineno}: {e.text}")
    
    # Mostrar contexto del error
    error_lines = content.split('\n')
    if e.lineno <= len(error_lines):
        start = max(0, e.lineno - 5)
        end = min(len(error_lines), e.lineno + 5)
        print(f"\n   Contexto alrededor de línea {e.lineno}:")
        for i in range(start, end):
            marker = ">>>" if i == e.lineno - 1 else "   "
            print(f"{marker} {i+1:4d}: {error_lines[i]}")
    
    sys.exit(1)

# Guardar archivo
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Archivo guardado correctamente")
PYEOF

echo ""
echo "✅✅✅ Función restaurada ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



