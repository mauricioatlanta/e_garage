#!/bin/bash
# Script para FORZAR la corrección de signup_complete.py
# Reemplaza directamente la sección problemática sin depender de patrones complejos

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 FORZANDO corrección en signup_complete.py..."

python3 << 'PYEOF'
file_path = "taller/views_extra/signup_complete.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar si ya tiene la corrección
if 'requires_email_verification' in content and 'return redirect("account_email_verification_sent")' in content:
    # Verificar que el redirect esté ANTES del login
    login_pos = content.find('login(')
    redirect_pos = content.find('return redirect("account_email_verification_sent")')
    
    if redirect_pos != -1 and login_pos != -1 and redirect_pos < login_pos:
        print("✅ El código ya está correcto: redirect antes de login")
        print("   Pero verificando que todo esté bien...")
    else:
        print("⚠️  PROBLEMA: El redirect está después del login")
        print("   Esto causa que se haga login antes de verificar email")
        print("   Aplicando corrección forzada...")
        
        # Buscar y reemplazar la sección completa desde crear empresa hasta el final de redirecciones
        # Patrón: desde suscripcion_activa hasta el último return redirect
        
        # Encontrar donde termina la creación de empresa
        empresa_end = content.find('suscripcion_activa=config["suscripcion_activa"],')
        if empresa_end != -1:
            # Encontrar el cierre del paréntesis de create
            paren_close = content.find(')', empresa_end)
            if paren_close != -1:
                # Buscar donde empieza el login
                login_start = content.find('# 🔥 PASO 4: LOGIN AUTOMÁTICO', paren_close)
                if login_start == -1:
                    login_start = content.find('login(', paren_close)
                
                if login_start != -1:
                    # Reemplazar desde después de crear empresa hasta antes del login
                    before = content[:paren_close+1]
                    after = content[login_start:]
                    
                    # Insertar el código de verificación
                    verification_code = '''
                    )

                    # 🔥 PASO 4: CREAR EmailAddress Y ENVIAR EMAIL DE VERIFICACIÓN (si se requiere)
                    requires_email_verification = getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "mandatory") == "mandatory"
                    
                    if requires_email_verification:
                        # Crear EmailAddress para allauth
                        try:
                            from allauth.account.models import EmailAddress
                            from allauth.account.utils import send_email_confirmation
                            
                            # Crear o obtener EmailAddress
                            email_address, created = EmailAddress.objects.get_or_create(
                                user=user,
                                email=email,
                                defaults={"verified": False, "primary": True}
                            )
                            
                            # Enviar email de confirmación
                            send_email_confirmation(request, user, email=email)
                        except Exception as e:
                            print(f"⚠️  Error creando EmailAddress o enviando email: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    # 🔥 PASO 5: VERIFICAR SI SE REQUIERE VERIFICACIÓN DE EMAIL
                    if requires_email_verification:
                        # NO hacer login automático - redirigir a página de confirmación
                        is_spanish = pais in {"CL", "MX", "CO", "PE", "VE", "EC"}
                        if is_spanish:
                            messages.success(
                                request,
                                "¡Cuenta creada exitosamente! Por favor, revisa tu email para activar tu cuenta."
                            )
                        else:
                            messages.success(
                                request,
                                "Account created successfully! Please check your email to activate your account."
                            )
                        # Redirigir a la página de confirmación de email
                        return redirect("account_email_verification_sent")
                    
                    # Si NO se requiere verificación, hacer login automático
                    # 🔥 PASO 6: LOGIN AUTOMÁTICO'''
                    
                    content = before + verification_code + after
                    print("✅ Código de verificación insertado")
else:
    print("❌ El código NO tiene la corrección aplicada")
    print("   Aplicando corrección completa...")
    
    # Buscar donde crear empresa termina
    empresa_pattern = 'suscripcion_activa=config["suscripcion_activa"],'
    empresa_pos = content.find(empresa_pattern)
    
    if empresa_pos != -1:
        # Encontrar el cierre del paréntesis
        paren_close = content.find(')', empresa_pos)
        if paren_close != -1:
            # Buscar donde empieza el login (puede ser "PASO 4" o directamente "login(")
            login_markers = [
                '# 🔥 PASO 4: LOGIN AUTOMÁTICO',
                '# PASO 4: LOGIN AUTOMÁTICO',
                'login('
            ]
            
            login_start = -1
            for marker in login_markers:
                pos = content.find(marker, paren_close)
                if pos != -1:
                    login_start = pos
                    break
            
            if login_start != -1:
                # Dividir el contenido
                before = content[:paren_close+1]
                after = content[login_start:]
                
                # Insertar código de verificación
                verification_code = '''
                    )

                    # 🔥 PASO 4: CREAR EmailAddress Y ENVIAR EMAIL DE VERIFICACIÓN (si se requiere)
                    requires_email_verification = getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "mandatory") == "mandatory"
                    
                    if requires_email_verification:
                        # Crear EmailAddress para allauth
                        try:
                            from allauth.account.models import EmailAddress
                            from allauth.account.utils import send_email_confirmation
                            
                            # Crear o obtener EmailAddress
                            email_address, created = EmailAddress.objects.get_or_create(
                                user=user,
                                email=email,
                                defaults={"verified": False, "primary": True}
                            )
                            
                            # Enviar email de confirmación
                            send_email_confirmation(request, user, email=email)
                        except Exception as e:
                            print(f"⚠️  Error creando EmailAddress o enviando email: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    # 🔥 PASO 5: VERIFICAR SI SE REQUIERE VERIFICACIÓN DE EMAIL
                    if requires_email_verification:
                        # NO hacer login automático - redirigir a página de confirmación
                        is_spanish = pais in {"CL", "MX", "CO", "PE", "VE", "EC"}
                        if is_spanish:
                            messages.success(
                                request,
                                "¡Cuenta creada exitosamente! Por favor, revisa tu email para activar tu cuenta."
                            )
                        else:
                            messages.success(
                                request,
                                "Account created successfully! Please check your email to activate your account."
                            )
                        # Redirigir a la página de confirmación de email
                        return redirect("account_email_verification_sent")
                    
                    # Si NO se requiere verificación, hacer login automático
                    # 🔥 PASO 6: LOGIN AUTOMÁTICO'''
                
                content = before + verification_code + after
                print("✅ Código de verificación insertado")
            else:
                print("❌ No se encontró donde empieza el login")
        else:
            print("❌ No se encontró el cierre del paréntesis")
    else:
        print("❌ No se encontró donde se crea la empresa")

# Verificar que tenga el import de settings
if 'from django.conf import settings' not in content:
    # Agregar después de otros imports
    if 'from django.utils.translation import activate' in content:
        content = content.replace(
            'from django.utils.translation import activate',
            'from django.utils.translation import activate\n\nfrom django.conf import settings'
        )
        print("✅ Import de settings agregado")
    else:
        print("⚠️  No se encontró donde agregar el import de settings")

# Guardar
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Archivo actualizado")
PYEOF

echo ""
echo "🔍 Verificando que la corrección se aplicó correctamente..."

python3 << 'PYEOF'
import os
import sys
import django

sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.conf import settings

# Verificar configuración
email_verification = getattr(settings, 'ACCOUNT_EMAIL_VERIFICATION', 'none')
print(f"📋 ACCOUNT_EMAIL_VERIFICATION: {email_verification}")

if email_verification != 'mandatory':
    print("⚠️  ADVERTENCIA: ACCOUNT_EMAIL_VERIFICATION no está en 'mandatory'")
    print("   Esto puede causar que se omita la verificación de email")
else:
    print("✅ ACCOUNT_EMAIL_VERIFICATION está configurado correctamente")
PYEOF

echo ""
echo "✅✅✅ Corrección aplicada ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"
echo ""
echo "📋 Próximos pasos:"
echo "  1. Prueba registrarte nuevamente"
echo "  2. Deberías ser redirigido a la página de confirmación de email"
echo "  3. NO deberías hacer login automático hasta verificar el email"



