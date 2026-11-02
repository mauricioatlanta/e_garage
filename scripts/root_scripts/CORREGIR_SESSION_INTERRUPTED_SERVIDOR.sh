#!/bin/bash
# Script para corregir el error SessionInterrupted eliminando request.session.save()

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Corrigiendo error SessionInterrupted..."

python3 << 'PYEOF'
file_path = "taller/views_extra/signup_complete.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar y reemplazar el bloque problemático
old_block = '''                    # 🔥 PASO 7: SI NO SE REQUIERE VERIFICACIÓN, HACER LOGIN AUTOMÁTICO
                    login(
                        request,
                        user,
                        backend="django.contrib.auth.backends.ModelBackend",
                    )

                    # Forzar guardado de la nueva sesión para evitar SessionInterrupted
                    request.session.save()'''

new_block = '''                    # 🔥 PASO 7: SI NO SE REQUIERE VERIFICACIÓN, HACER LOGIN AUTOMÁTICO
                    login(
                        request,
                        user,
                        backend="django.contrib.auth.backends.ModelBackend",
                    )
                    # Nota: No llamar request.session.save() explícitamente
                    # Django guarda la sesión automáticamente al final de la request
                    # Hacerlo dentro de una transacción puede causar "database is locked" con SQLite'''

if old_block in content:
    content = content.replace(old_block, new_block)
    print("✅ Bloque de sesión actualizado")
else:
    # Buscar variaciones
    if 'request.session.save()' in content:
        # Buscar el contexto alrededor
        lines = content.split('\n')
        new_lines = []
        i = 0
        found = False
        while i < len(lines):
            line = lines[i]
            if 'request.session.save()' in line:
                found = True
                # Remover esta línea y las líneas de comentario relacionadas
                # Buscar hacia atrás para encontrar el comentario
                j = i - 1
                while j >= 0 and (lines[j].strip().startswith('#') or lines[j].strip() == ''):
                    j -= 1
                # Mantener las líneas hasta antes del comentario sobre session.save
                # y agregar el nuevo comentario
                new_lines.append('                    # Nota: No llamar request.session.save() explícitamente\n')
                new_lines.append('                    # Django guarda la sesión automáticamente al final de la request\n')
                new_lines.append('                    # Hacerlo dentro de una transacción puede causar "database is locked" con SQLite\n')
                i += 1
                # Saltar la línea de request.session.save() y líneas vacías siguientes
                while i < len(lines) and (lines[i].strip() == '' or lines[i].strip().startswith('#')):
                    i += 1
                continue
            new_lines.append(line)
            i += 1
        
        if found:
            content = '\n'.join(new_lines)
            print("✅ request.session.save() removido")
        else:
            print("⚠️  No se encontró request.session.save()")
    else:
        print("ℹ️  request.session.save() no existe en el archivo")

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
echo "  - request.session.save() removido (causaba 'database is locked' con SQLite)"
echo "  - Django guarda la sesión automáticamente al final de la request"
echo "  - Error SessionInterrupted debería estar resuelto"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"
echo ""
echo "🧪 Para probar:"
echo "  1. Ir a https://www.egarage.cl/accounts/signup/?from=cl"
echo "  2. Completar el formulario"
echo "  3. NO debería aparecer el error SessionInterrupted"
echo "  4. Debería redirigir correctamente a la página de confirmación"



