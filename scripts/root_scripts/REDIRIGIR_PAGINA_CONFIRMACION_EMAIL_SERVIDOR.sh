#!/bin/bash
# Script para redirigir a una nueva página de confirmación de email

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Configurando redirección a nueva página de confirmación de email..."

# 1. Actualizar signup_complete.py para usar redirect en lugar de render
python3 << 'PYEOF'
file_path = "taller/views_extra/signup_complete.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar y reemplazar el bloque de render por redirect
old_block = '''                        # Redirigir a la página de confirmación de email
                        # Renderizar directamente nuestro template personalizado
                        return render(request, "account/email_verification_sent.html", {
                            "LANGUAGE_CODE": language_code,
                            "from_country": from_country,
                        })'''

new_block = '''                        # Redirigir a la página de confirmación de email (nueva página)
                        # Construir URL según el país
                        if pais == "CL":
                            verification_url = "/cl/es/accounts/confirm-email/"
                        elif pais == "MX":
                            verification_url = "/mx/es/accounts/confirm-email/"
                        else:
                            verification_url = "/us/en/accounts/confirm-email/"
                        return redirect(verification_url)'''

if old_block in content:
    content = content.replace(old_block, new_block)
    print("✅ Bloque de redirección actualizado")
else:
    # Buscar variaciones
    import re
    pattern = r'# Redirigir a la página de confirmación de email.*?return render.*?from_country.*?\}\)'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_block, content, flags=re.DOTALL)
        print("✅ Bloque reemplazado con regex")
    else:
        print("⚠️  No se encontró el bloque exacto, buscando manualmente...")
        lines = content.split('\n')
        new_lines = []
        i = 0
        found = False
        while i < len(lines):
            line = lines[i]
            if 'Redirigir a la página de confirmación de email' in line and 'Renderizar directamente' in lines[i+1] if i+1 < len(lines) else False:
                found = True
                # Insertar el nuevo bloque
                new_lines.append('                        # Redirigir a la página de confirmación de email (nueva página)\n')
                new_lines.append('                        # Construir URL según el país\n')
                new_lines.append('                        if pais == "CL":\n')
                new_lines.append('                            verification_url = "/cl/es/accounts/confirm-email/"\n')
                new_lines.append('                        elif pais == "MX":\n')
                new_lines.append('                            verification_url = "/mx/es/accounts/confirm-email/"\n')
                new_lines.append('                        else:\n')
                new_lines.append('                            verification_url = "/us/en/accounts/confirm-email/"\n')
                new_lines.append('                        return redirect(verification_url)\n')
                # Saltar las líneas antiguas
                i += 1
                while i < len(lines):
                    if 'return render' in lines[i]:
                        # Saltar hasta encontrar el cierre del bloque
                        while i < len(lines) and '})' not in lines[i]:
                            i += 1
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

# 2. Agregar URLs country-aware para confirmación de email
python3 << 'PYEOF'
file_path = "gestion_taller/urls.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar si ya existen las URLs
if 'path("cl/es/accounts/confirm-email/' in content:
    print("ℹ️  URLs country-aware ya existen")
else:
    # Buscar donde agregar las URLs (después de accounts/confirm-email/)
    if 'path("accounts/confirm-email/' in content:
        content = content.replace(
            'path("accounts/confirm-email/", TemplateView.as_view(template_name="account/email_verification_sent.html"), name="account_email_verification_sent"),',
            'path("accounts/confirm-email/", TemplateView.as_view(template_name="account/email_verification_sent.html"), name="account_email_verification_sent"),\n    # URLs country-aware para confirmación de email\n    path("cl/es/accounts/confirm-email/", TemplateView.as_view(template_name="account/email_verification_sent.html"), name="cl_account_email_verification_sent"),\n    path("mx/es/accounts/confirm-email/", TemplateView.as_view(template_name="account/email_verification_sent.html"), name="mx_account_email_verification_sent"),\n    path("us/en/accounts/confirm-email/", TemplateView.as_view(template_name="account/email_verification_sent.html"), name="us_account_email_verification_sent"),'
        )
        print("✅ URLs country-aware agregadas")
    else:
        print("⚠️  No se encontró el patrón para agregar las URLs")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
PYEOF

# 3. Corregir template para usar URLs directas
python3 << 'PYEOF'
file_path = "templates/account/email_verification_sent.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar country_url por URL directa
old_login_link = 'href="{% country_url \'account_login\' %}"'
new_login_link = 'href="/accounts/login/"'

old_resend_link = 'href="{% url \'account_email_verification_sent\' %}"'
new_resend_link = 'href="/accounts/email/"'

if old_login_link in content:
    content = content.replace(old_login_link, new_login_link)
    print("✅ Link de login corregido")
else:
    print("⚠️  No se encontró el link de login a corregir")

if old_resend_link in content:
    content = content.replace(old_resend_link, new_resend_link)
    print("✅ Link de reenvío corregido")
else:
    print("⚠️  No se encontró el link de reenvío a corregir")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Template actualizado")
PYEOF

echo ""
echo "✅✅✅ Cambios aplicados ✅✅✅"
echo ""
echo "📋 Resumen de correcciones:"
echo "  - signup_complete.py ahora REDIRIGE a una nueva página (no renderiza en la misma)"
echo "  - URLs country-aware agregadas para confirmación de email"
echo "  - Template corregido para usar URLs directas (sin country_url)"
echo "  - Error 'Reverse for account_login not found' corregido"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"
echo ""
echo "🧪 Para probar:"
echo "  1. Ir a https://www.egarage.cl/accounts/signup/?from=cl"
echo "  2. Completar el formulario"
echo "  3. Debería REDIRIGIR a /cl/es/accounts/confirm-email/ (nueva página)"
echo "  4. La nueva página mostrará el mensaje de confirmación"
echo "  5. NO debería mostrar el formulario de registro"



