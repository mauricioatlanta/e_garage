#!/bin/bash
# Script para restaurar la función enviar_documento_whatsapp completa

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Restaurando función enviar_documento_whatsapp..."

python3 << 'PYEOF'
file_path = "taller/documentos/views.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Función completa correcta
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
    )'''

# Buscar la función en el contenido
import re

# Patrón para encontrar la función completa
pattern = r'def enviar_documento_whatsapp\(request, documento_id\):.*?return JsonResponse\(\s*\{[^}]*"mensaje": mensaje,[^}]*\}\s*\)'

# Intentar encontrar y reemplazar
if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, funcion_correcta, content, flags=re.DOTALL)
    print("✅ Función reemplazada con regex")
else:
    # Método manual: buscar inicio y fin de la función
    lines = content.split('\n')
    func_start = None
    func_end = None
    
    for i, line in enumerate(lines):
        if 'def enviar_documento_whatsapp' in line:
            func_start = i
        elif func_start is not None and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
            # Si encontramos una línea no indentada después de la función, es el final
            if not line.strip().startswith('#') and not line.strip().startswith('"""'):
                func_end = i
                break
    
    if func_start is None:
        print("❌ No se encontró la función enviar_documento_whatsapp")
        sys.exit(1)
    
    if func_end is None:
        func_end = len(lines)
    
    print(f"📍 Función encontrada desde línea {func_start + 1} hasta línea {func_end}")
    
    # Reemplazar la función
    new_lines = lines[:func_start] + funcion_correcta.split('\n') + lines[func_end:]
    content = '\n'.join(new_lines)
    print("✅ Función reemplazada manualmente")

# Verificar sintaxis
import ast
try:
    ast.parse(content)
    print("✅ Sintaxis verificada correctamente")
except SyntaxError as e:
    print(f"❌ Error de sintaxis: {e}")
    print(f"   Línea {e.lineno}: {e.text}")
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



