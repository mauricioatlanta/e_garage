#!/bin/bash
# Solución final: restaurar función completa desde versión correcta

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Aplicando solución final para indentación en views.py..."

# Hacer backup
cp taller/documentos/views.py taller/documentos/views.py.backup_$(date +%Y%m%d_%H%M%S)

python3 << 'PYEOF'
import sys
import ast
import re

file_path = "taller/documentos/views.py"

# Leer archivo
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar sintaxis
try:
    ast.parse(content)
    print("✅ El archivo ya tiene sintaxis correcta")
    sys.exit(0)
except SyntaxError as e:
    print(f"❌ Error de sintaxis: {e}")
    print(f"   Línea {e.lineno}: {e.text}")
    
    # Función correcta completa
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

    # Buscar y reemplazar la función usando regex
    # Patrón que busca desde def hasta el último return JsonResponse con mensaje
    pattern = r'def enviar_documento_whatsapp\(request, documento_id\):.*?return JsonResponse\(\s*\{[^}]*"mensaje": mensaje,[^}]*\}\s*\)'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, funcion_correcta, content, flags=re.DOTALL)
        print("✅ Función reemplazada con regex")
    else:
        # Método manual: buscar líneas
        lines = content.split('\n')
        func_start = None
        func_end = None
        
        for i, line in enumerate(lines):
            if 'def enviar_documento_whatsapp' in line:
                func_start = i
            elif func_start is not None:
                # Buscar el final: siguiente función o clase al mismo nivel
                stripped = line.lstrip()
                if stripped and not line.startswith(' ') and not line.startswith('\t'):
                    if stripped.startswith('def ') or stripped.startswith('class '):
                        func_end = i
                        break
                # O buscar el cierre del último return JsonResponse
                if 'return JsonResponse(' in line and 'mensaje": mensaje' in ''.join(lines[max(0, i-5):i+10]):
                    # Buscar el cierre del JsonResponse (7 líneas después aproximadamente)
                    for j in range(i, min(i+10, len(lines))):
                        if lines[j].strip() == ')' and j > i:
                            func_end = j + 1
                            break
        
        if func_start is None:
            print("❌ No se encontró la función")
            sys.exit(1)
        
        if func_end is None:
            func_end = func_start + 80  # Asumir máximo 80 líneas
        
        print(f"📍 Reemplazando líneas {func_start+1} a {func_end}")
        
        # Reemplazar
        new_lines = lines[:func_start] + funcion_correcta.split('\n') + [''] + lines[func_end:]
        content = '\n'.join(new_lines)
        print("✅ Función reemplazada manualmente")
    
    # Verificar sintaxis
    try:
        ast.parse(content)
        print("✅ Sintaxis verificada correctamente")
    except SyntaxError as e2:
        print(f"❌ Error persistente: {e2}")
        print(f"   Línea {e2.lineno}: {e2.text}")
        
        # Mostrar más contexto
        error_lines = content.split('\n')
        if e2.lineno <= len(error_lines):
            start = max(0, e2.lineno - 10)
            end = min(len(error_lines), e2.lineno + 10)
            print(f"\n   Contexto (líneas {start+1} a {end}):")
            for i in range(start, end):
                marker = ">>>" if i == e2.lineno - 1 else "   "
                indent = len(error_lines[i]) - len(error_lines[i].lstrip())
                print(f"{marker} {i+1:4d} [{indent:2d}]: {error_lines[i][:80]}")
        
        sys.exit(1)
    
    # Guardar
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Archivo guardado correctamente")
PYEOF

echo ""
echo "✅✅✅ Corrección aplicada ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



