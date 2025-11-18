#!/usr/bin/env python3
"""
Solución directa: Reemplaza las líneas 1195-1227 con el código correcto
Lee el patrón correcto y lo aplica directamente
"""
import os

file_path = "taller/documentos/views.py"

print("═══════════════════════════════════════════════════════════════")
print("  SOLUCIÓN DIRECTA: REEMPLAZO DE LÍNEAS ESPECÍFICAS")
print("═══════════════════════════════════════════════════════════════")

if not os.path.exists(file_path):
    print(f"❌ Error: {file_path} no encontrado")
    exit(1)

# Crear backup
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

backup_path = f"{file_path}.backup_antes_lineas"
with open(backup_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)
print(f"📦 Backup creado: {backup_path}")

# Código correcto (líneas 1195-1227)
# Basado en la versión local que funciona
correct_code = """    mensaje = f"""Hola {documento.cliente.nombre},

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
    mensaje_encoded = mensaje.replace(" ", "%20").replace("\\n", "%0A")
    url_whatsapp = f"https://wa.me/{telefono}?text={mensaje_encoded}"

    return JsonResponse(
        {
            "success": True,
            "url_whatsapp": url_whatsapp,
            "telefono": telefono,
            "mensaje": mensaje,
        }
    )
"""

# Buscar el inicio del bloque (línea con "mensaje = f"""")
start_idx = None
for i, line in enumerate(lines):
    if 'mensaje = f"""' in line and i >= 1190:
        start_idx = i
        print(f"✅ Inicio encontrado en línea {i+1}")
        print(f"   {line.strip()[:80]}")
        break

if start_idx is None:
    print("⚠️  No se encontró el inicio del bloque")
    print("   Buscando en un rango más amplio...")
    for i in range(1190, min(len(lines), 1205)):
        print(f"   {i+1}: {lines[i].strip()[:100]}")
    exit(1)

# Buscar el final del bloque (línea con "return JsonResponse")
end_idx = None
for i in range(start_idx + 10, min(len(lines), start_idx + 40)):
    if 'return JsonResponse' in lines[i]:
        end_idx = i
        print(f"✅ Fin encontrado en línea {i+1}")
        break

if end_idx is None:
    print("⚠️  No se encontró el final del bloque")
    # Buscar manualmente
    for i in range(start_idx + 15, min(len(lines), start_idx + 35)):
        print(f"   {i+1}: {lines[i].strip()[:100]}")
    exit(1)

print(f"\n📋 Reemplazando líneas {start_idx+1} a {end_idx+1}")

# Obtener indentación de la primera línea
first_line = lines[start_idx]
indent = len(first_line) - len(first_line.lstrip())
indent_str = ' ' * indent

# Aplicar indentación al código correcto
correct_lines = [indent_str + line if line.strip() else line 
                 for line in correct_code.splitlines(True)]

# Reemplazar
new_lines = lines[:start_idx] + correct_lines + lines[end_idx+1:]

# Escribir archivo
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Archivo actualizado")

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

print("\n✅ Proceso completado exitosamente")

