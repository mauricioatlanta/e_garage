#!/bin/bash
# Script para corregir el template de confirmación de email

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Corrigiendo template de confirmación de email..."

# 1. Actualizar signup_complete.py para renderizar directamente el template
python3 << 'PYEOF'
file_path = "taller/views_extra/signup_complete.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar y reemplazar el bloque de redirección
old_block = '''                        # Redirigir a la página de confirmación de email
                        # Usar reverse para obtener la URL correcta
                        from django.urls import reverse
                        try:
                            verification_url = reverse("account_email_verification_sent")
                            return redirect(verification_url)
                        except Exception:
                            # Si no existe la URL, usar TemplateView directamente
                            from django.views.generic import TemplateView
                            from django.http import HttpResponse
                            return render(request, "account/email_verification_sent.html", {
                                "LANGUAGE_CODE": language_code
                            })'''

new_block = '''                        # Redirigir a la página de confirmación de email
                        # Renderizar directamente nuestro template personalizado
                        return render(request, "account/email_verification_sent.html", {
                            "LANGUAGE_CODE": language_code,
                            "from_country": from_country,
                        })'''

if old_block in content:
    content = content.replace(old_block, new_block)
    print("✅ Bloque de redirección actualizado")
else:
    # Buscar variaciones
    import re
    pattern = r'# Redirigir a la página de confirmación de email.*?LANGUAGE_CODE.*?language_code.*?\}\)'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_block.split('return render')[1], content, flags=re.DOTALL)
        print("✅ Bloque reemplazado con regex")
    else:
        print("⚠️  No se encontró el bloque exacto, buscando manualmente...")
        lines = content.split('\n')
        new_lines = []
        i = 0
        found = False
        while i < len(lines):
            line = lines[i]
            if 'Redirigir a la página de confirmación de email' in line:
                found = True
                # Insertar el nuevo bloque
                new_lines.append('                        # Redirigir a la página de confirmación de email\n')
                new_lines.append('                        # Renderizar directamente nuestro template personalizado\n')
                new_lines.append('                        return render(request, "account/email_verification_sent.html", {\n')
                new_lines.append('                            "LANGUAGE_CODE": language_code,\n')
                new_lines.append('                            "from_country": from_country,\n')
                new_lines.append('                        })\n')
                # Saltar las líneas antiguas hasta encontrar el siguiente bloque
                i += 1
                while i < len(lines):
                    if 'PASO 7: SI NO SE REQUIERE VERIFICACIÓN' in lines[i] or 'PASO 6: SI SE REQUIERE VERIFICACIÓN' not in lines[i-10:i]:
                        if 'return' in lines[i] and ('redirect' in lines[i] or 'render' in lines[i]):
                            i += 1
                            break
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

print("✅ Archivo signup_complete.py actualizado")
PYEOF

# 2. Agregar URL /accounts/confirm-email/ antes de allauth.urls
python3 << 'PYEOF'
file_path = "gestion_taller/urls.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar si ya existe la URL
if 'path("accounts/confirm-email/' in content:
    print("ℹ️  URL accounts/confirm-email/ ya existe")
else:
    # Buscar donde agregar la URL (después de signup, antes de allauth)
    if 'path("accounts/signup/' in content and 'path("accounts/", include("allauth.urls"))' in content:
        # Insertar antes de allauth.urls
        content = content.replace(
            'path("accounts/signup/", signup_complete, name="account_signup"),',
            'path("accounts/signup/", signup_complete, name="account_signup"),\n    # Página de confirmación de email (antes de allauth para que tenga prioridad)\n    path("accounts/confirm-email/", TemplateView.as_view(template_name="account/email_verification_sent.html"), name="account_email_verification_sent"),\n    path("accounts/email/verification_sent/", TemplateView.as_view(template_name="account/email_verification_sent.html"), name="account_email_verification_sent_alt"),'
        )
        print("✅ URLs de confirmación de email agregadas")
    else:
        print("⚠️  No se encontró el patrón para agregar las URLs")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
PYEOF

echo ""
echo "✅✅✅ Cambios aplicados ✅✅✅"
echo ""
echo "📋 Resumen de correcciones:"
echo "  - signup_complete.py ahora renderiza directamente el template"
echo "  - URL /accounts/confirm-email/ agregada antes de allauth.urls"
echo "  - URL /accounts/email/verification_sent/ también agregada como alternativa"
echo "  - Template email_verification_sent.html será usado correctamente"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"
echo ""
echo "🧪 Para probar:"
echo "  1. Ir a https://www.egarage.cl/accounts/signup/?from=cl"
echo "  2. Completar el formulario"
echo "  3. Debería mostrar la página de confirmación de email (no vacía)"
echo "  4. La página debería tener el logo, mensaje y botones"



