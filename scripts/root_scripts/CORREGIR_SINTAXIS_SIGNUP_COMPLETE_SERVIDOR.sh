#!/bin/bash
# Script para corregir el error de sintaxis en signup_complete.py

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Corrigiendo error de sintaxis en signup_complete.py..."

python3 << 'PYEOF'
import sys
import ast

file_path = "taller/views_extra/signup_complete.py"

# Leer el archivo
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar sintaxis
try:
    ast.parse(content)
    print("✅ La sintaxis del archivo es correcta")
except SyntaxError as e:
    print(f"❌ Error de sintaxis encontrado: {e}")
    print(f"   Línea {e.lineno}: {e.text}")
    print(f"   Mensaje: {e.msg}")
    
    # Intentar corregir el problema común: llaves no cerradas
    lines = content.split('\n')
    
    # Contar llaves
    open_braces = content.count('{')
    close_braces = content.count('}')
    
    print(f"   Llaves abiertas: {open_braces}, cerradas: {close_braces}")
    
    if open_braces > close_braces:
        print("   ⚠️  Hay más llaves abiertas que cerradas")
        # Buscar el contexto alrededor del error
        error_line = e.lineno - 1
        start = max(0, error_line - 5)
        end = min(len(lines), error_line + 5)
        print(f"\n   Contexto alrededor de la línea {e.lineno}:")
        for i in range(start, end):
            marker = ">>>" if i == error_line else "   "
            print(f"{marker} {i+1:4d}: {lines[i]}")
    
    sys.exit(1)

# Si llegamos aquí, la sintaxis es correcta
print("✅ Archivo verificado correctamente")
PYEOF

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Se encontró un error de sintaxis. Restaurando desde Git..."
    
    # Restaurar desde Git
    git checkout HEAD -- taller/views_extra/signup_complete.py
    
    echo "✅ Archivo restaurado desde Git"
    echo ""
    echo "🔄 Aplicando corrección manual..."
    
    # Aplicar la corrección manualmente
    python3 << 'PYEOF'
file_path = "taller/views_extra/signup_complete.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar el bloque que necesita ser reemplazado
# Buscar la línea con "PASO 4: CREAR EmailAddress"
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Si encontramos el bloque problemático, reemplazarlo
    if 'PASO 4: CREAR EmailAddress Y ENVIAR EMAIL DE VERIFICACIÓN' in line:
        # Saltar hasta encontrar el bloque correcto
        # Insertar el código corregido
        new_lines.append('                    # 🔥 PASO 4: VERIFICAR SI SE REQUIERE VERIFICACIÓN DE EMAIL\n')
        new_lines.append('                    # SIEMPRE verificar la configuración de settings\n')
        new_lines.append('                    requires_email_verification = getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "mandatory") == "mandatory"\n')
        new_lines.append('                    \n')
        new_lines.append('                    # 🔥 PASO 5: CREAR EmailAddress Y ENVIAR EMAIL DE VERIFICACIÓN\n')
        new_lines.append('                    if requires_email_verification:\n')
        new_lines.append('                        # Crear EmailAddress para allauth\n')
        new_lines.append('                        try:\n')
        new_lines.append('                            from allauth.account.models import EmailAddress\n')
        new_lines.append('                            from allauth.account.utils import send_email_confirmation\n')
        new_lines.append('                            \n')
        new_lines.append('                            # Crear o obtener EmailAddress\n')
        new_lines.append('                            email_address, created = EmailAddress.objects.get_or_create(\n')
        new_lines.append('                                user=user,\n')
        new_lines.append('                                email=email,\n')
        new_lines.append('                                defaults={"verified": False, "primary": True}\n')
        new_lines.append('                            )\n')
        new_lines.append('                            \n')
        new_lines.append('                            # Si ya existe pero está verificado, no hacer nada\n')
        new_lines.append('                            if not email_address.verified:\n')
        new_lines.append('                                # Enviar email de confirmación\n')
        new_lines.append('                                send_email_confirmation(request, user, email=email)\n')
        new_lines.append('                        except Exception as e:\n')
        new_lines.append('                            print(f"⚠️  Error creando EmailAddress o enviando email: {e}")\n')
        new_lines.append('                            import traceback\n')
        new_lines.append('                            traceback.print_exc()\n')
        new_lines.append('                    \n')
        new_lines.append('                    # 🔥 PASO 6: SI SE REQUIERE VERIFICACIÓN, NO HACER LOGIN - REDIRIGIR A CONFIRMACIÓN\n')
        new_lines.append('                    if requires_email_verification:\n')
        new_lines.append('                        # NO hacer login automático - redirigir a página de confirmación\n')
        new_lines.append('                        is_spanish = pais in {"CL", "MX", "CO", "PE", "VE", "EC"}\n')
        new_lines.append('                        if is_spanish:\n')
        new_lines.append('                            messages.success(\n')
        new_lines.append('                                request,\n')
        new_lines.append('                                "¡Cuenta creada exitosamente! Por favor, revisa tu email para activar tu cuenta."\n')
        new_lines.append('                            )\n')
        new_lines.append('                        else:\n')
        new_lines.append('                            messages.success(\n')
        new_lines.append('                                request,\n')
        new_lines.append('                                "Account created successfully! Please check your email to activate your account."\n')
        new_lines.append('                            )\n')
        new_lines.append('                        # Redirigir a la página de confirmación de email\n')
        new_lines.append('                        # Usar reverse para obtener la URL correcta\n')
        new_lines.append('                        from django.urls import reverse\n')
        new_lines.append('                        try:\n')
        new_lines.append('                            verification_url = reverse("account_email_verification_sent")\n')
        new_lines.append('                            return redirect(verification_url)\n')
        new_lines.append('                        except Exception:\n')
        new_lines.append('                            # Si no existe la URL, renderizar el template directamente\n')
        new_lines.append('                            return render(request, "account/email_verification_sent.html", {\n')
        new_lines.append('                                "LANGUAGE_CODE": language_code\n')
        new_lines.append('                            })\n')
        new_lines.append('                    \n')
        new_lines.append('                    # 🔥 PASO 7: SI NO SE REQUIERE VERIFICACIÓN, HACER LOGIN AUTOMÁTICO\n')
        
        # Saltar las líneas del bloque antiguo hasta encontrar el siguiente paso
        i += 1
        while i < len(lines):
            if 'PASO 6: LOGIN AUTOMÁTICO' in lines[i] or 'PASO 7: SI NO SE REQUIERE VERIFICACIÓN' in lines[i]:
                # Continuar desde aquí
                break
            i += 1
        continue
    else:
        new_lines.append(line)
        i += 1

# Escribir el archivo corregido
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ Archivo corregido")
PYEOF

    # Verificar sintaxis nuevamente
    python3 << 'PYEOF'
import ast

file_path = "taller/views_extra/signup_complete.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

try:
    ast.parse(content)
    print("✅✅✅ Sintaxis verificada correctamente")
except SyntaxError as e:
    print(f"❌❌❌ Aún hay errores de sintaxis: {e}")
    sys.exit(1)
PYEOF
fi

echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



