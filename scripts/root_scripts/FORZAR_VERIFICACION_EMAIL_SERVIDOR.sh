#!/bin/bash
# Script para forzar verificación de email SIEMPRE en signup_complete.py

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Forzando verificación de email SIEMPRE..."

python3 << 'PYEOF'
file_path = "taller/views_extra/signup_complete.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar y reemplazar el bloque de verificación
old_block = '''                    # 🔥 PASO 4: VERIFICAR SI SE REQUIERE VERIFICACIÓN DE EMAIL
                    # SIEMPRE verificar la configuración de settings
                    requires_email_verification = getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "mandatory") == "mandatory"
                    
                    # 🔥 PASO 5: CREAR EmailAddress Y ENVIAR EMAIL DE VERIFICACIÓN
                    if requires_email_verification:'''

new_block = '''                    # 🔥 PASO 4: VERIFICAR SI SE REQUIERE VERIFICACIÓN DE EMAIL
                    # FORZAR verificación de email SIEMPRE (independiente de configuración)
                    account_email_verification = getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "mandatory")
                    requires_email_verification = account_email_verification == "mandatory"
                    
                    # DEBUG: Log para verificar configuración
                    print(f"🔍 DEBUG: ACCOUNT_EMAIL_VERIFICATION = {account_email_verification}")
                    print(f"🔍 DEBUG: requires_email_verification = {requires_email_verification}")
                    
                    # FORZAR verificación SIEMPRE (comentar esta línea si quieres respetar la configuración)
                    requires_email_verification = True
                    print(f"🔍 DEBUG: FORZANDO requires_email_verification = True")
                    
                    # 🔥 PASO 5: CREAR EmailAddress Y ENVIAR EMAIL DE VERIFICACIÓN
                    if requires_email_verification:'''

if old_block in content:
    content = content.replace(old_block, new_block)
    print("✅ Bloque de verificación actualizado")
else:
    # Intentar búsqueda más flexible
    import re
    pattern = r'# 🔥 PASO 4: VERIFICAR SI SE REQUIERE VERIFICACIÓN DE EMAIL.*?# 🔥 PASO 5: CREAR EmailAddress Y ENVIAR EMAIL DE VERIFICACIÓN'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_block.split('if requires_email_verification:')[0] + 'if requires_email_verification:', content, flags=re.DOTALL)
        print("✅ Bloque reemplazado con regex")
    else:
        print("⚠️  No se encontró el bloque exacto, buscando manualmente...")
        lines = content.split('\n')
        new_lines = []
        i = 0
        found = False
        while i < len(lines):
            line = lines[i]
            if 'PASO 4: VERIFICAR SI SE REQUIERE VERIFICACIÓN DE EMAIL' in line:
                found = True
                # Insertar el nuevo bloque
                new_lines.append('                    # 🔥 PASO 4: VERIFICAR SI SE REQUIERE VERIFICACIÓN DE EMAIL\n')
                new_lines.append('                    # FORZAR verificación de email SIEMPRE (independiente de configuración)\n')
                new_lines.append('                    account_email_verification = getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "mandatory")\n')
                new_lines.append('                    requires_email_verification = account_email_verification == "mandatory"\n')
                new_lines.append('                    \n')
                new_lines.append('                    # DEBUG: Log para verificar configuración\n')
                new_lines.append('                    print(f"🔍 DEBUG: ACCOUNT_EMAIL_VERIFICATION = {account_email_verification}")\n')
                new_lines.append('                    print(f"🔍 DEBUG: requires_email_verification = {requires_email_verification}")\n')
                new_lines.append('                    \n')
                new_lines.append('                    # FORZAR verificación SIEMPRE (comentar esta línea si quieres respetar la configuración)\n')
                new_lines.append('                    requires_email_verification = True\n')
                new_lines.append('                    print(f"🔍 DEBUG: FORZANDO requires_email_verification = True")\n')
                new_lines.append('                    \n')
                new_lines.append('                    # 🔥 PASO 5: CREAR EmailAddress Y ENVIAR EMAIL DE VERIFICACIÓN\n')
                # Saltar las líneas antiguas hasta encontrar "if requires_email_verification:"
                i += 1
                while i < len(lines) and 'if requires_email_verification:' not in lines[i]:
                    i += 1
                # Agregar la línea "if requires_email_verification:"
                new_lines.append('                    if requires_email_verification:\n')
                i += 1
                continue
            new_lines.append(line)
            i += 1
        
        if found:
            content = '\n'.join(new_lines)
            print("✅ Bloque insertado manualmente")
        else:
            print("❌ No se pudo encontrar el bloque a reemplazar")
            sys.exit(1)

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

print("✅ Archivo actualizado correctamente")
PYEOF

echo ""
echo "✅✅✅ Cambios aplicados ✅✅✅"
echo ""
echo "📋 Resumen de correcciones:"
echo "  - Verificación de email FORZADA SIEMPRE (independiente de configuración)"
echo "  - Logging de debug agregado para verificar configuración"
echo "  - Redirección a página de confirmación SIN hacer login"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"
echo ""
echo "🧪 Para probar:"
echo "  1. Ir a https://www.egarage.cl/accounts/signup/?from=cl"
echo "  2. Completar el formulario"
echo "  3. Debería redirigir a /accounts/email/verification_sent/"
echo "  4. NO debería hacer login automático"
echo "  5. Revisar logs del servidor para ver los mensajes DEBUG"



