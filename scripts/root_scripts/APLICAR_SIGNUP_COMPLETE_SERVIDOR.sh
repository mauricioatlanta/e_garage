#!/bin/bash
# Script simple para aplicar los cambios de signup_complete.py en el servidor
# Reemplaza directamente la sección problemática

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Aplicando correcciones en signup_complete.py..."

python3 << 'PYEOF'
file_path = "taller/views_extra/signup_complete.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Verificar si ya tiene la corrección
has_fix = False
for i, line in enumerate(lines):
    if 'requires_email_verification' in line and 'account_email_verification_sent' in ''.join(lines[max(0,i-10):i+10]):
        has_fix = True
        break

if has_fix:
    print("✅ El archivo ya tiene la corrección aplicada")
    print("🔍 Verificando que la lógica esté correcta...")
    
    # Verificar que el return redirect esté antes del login
    content = ''.join(lines)
    if 'return redirect("account_email_verification_sent")' in content:
        login_pos = content.find('login(')
        redirect_pos = content.find('return redirect("account_email_verification_sent")')
        
        if redirect_pos < login_pos:
            print("✅ La lógica está correcta: redirect antes de login")
        else:
            print("⚠️  ADVERTENCIA: El redirect está después del login")
            print("   Esto puede causar que se haga login antes de verificar email")
    else:
        print("❌ No se encontró el redirect a account_email_verification_sent")
else:
    print("⚠️  No se encontró la corrección, aplicando cambios...")
    
    # Buscar la línea donde está el login automático
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Buscar donde empieza el login automático (después de crear empresa)
        if 'suscripcion_activa=config["suscripcion_activa"]' in line:
            new_lines.append(line)
            i += 1
            # Buscar el cierre del paréntesis
            while i < len(lines) and ')' not in lines[i]:
                new_lines.append(lines[i])
                i += 1
            if i < len(lines):
                new_lines.append(lines[i])  # Agregar el cierre
                i += 1
            
            # Insertar el código de verificación de email
            new_lines.append('                    \n')
            new_lines.append('                    # 🔥 PASO 4: CREAR EmailAddress Y ENVIAR EMAIL DE VERIFICACIÓN (si se requiere)\n')
            new_lines.append('                    requires_email_verification = getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "mandatory") == "mandatory"\n')
            new_lines.append('                    \n')
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
            new_lines.append('                            # Enviar email de confirmación\n')
            new_lines.append('                            send_email_confirmation(request, user, email=email)\n')
            new_lines.append('                        except Exception as e:\n')
            new_lines.append('                            print(f"⚠️  Error creando EmailAddress o enviando email: {e}")\n')
            new_lines.append('                            import traceback\n')
            new_lines.append('                            traceback.print_exc()\n')
            new_lines.append('                    \n')
            new_lines.append('                    # 🔥 PASO 5: VERIFICAR SI SE REQUIERE VERIFICACIÓN DE EMAIL\n')
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
            new_lines.append('                        return redirect("account_email_verification_sent")\n')
            new_lines.append('                    \n')
            new_lines.append('                    # Si NO se requiere verificación, hacer login automático\n')
            new_lines.append('                    # 🔥 PASO 6: LOGIN AUTOMÁTICO\n')
            continue
        
        new_lines.append(line)
        i += 1
    
    # Verificar que se agregó el import de settings
    content_str = ''.join(new_lines)
    if 'from django.conf import settings' not in content_str:
        # Agregar el import
        for j, l in enumerate(new_lines):
            if 'from django.utils.translation import activate' in l:
                new_lines.insert(j+1, '\n')
                new_lines.insert(j+2, 'from django.conf import settings\n')
                break
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ Cambios aplicados")
PYEOF

echo ""
echo "✅✅✅ Proceso completado ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"



