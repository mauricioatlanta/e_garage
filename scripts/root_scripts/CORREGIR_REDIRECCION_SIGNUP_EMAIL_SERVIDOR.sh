#!/bin/bash
# Script para corregir la redirección después del registro para mostrar confirmación de email

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Corrigiendo redirección después del registro..."

python3 << 'PYEOF'
file_path = "taller/views_extra/signup_complete.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar si ya tiene la corrección
if 'PASO 6: SI SE REQUIERE VERIFICACIÓN, NO HACER LOGIN' in content:
    print("ℹ️  El código ya tiene la corrección aplicada")
else:
    # Buscar el bloque que necesita ser reemplazado
    old_block = '''                    # 🔥 PASO 4: CREAR EmailAddress Y ENVIAR EMAIL DE VERIFICACIÓN (si se requiere)
                    requires_email_verification = getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "mandatory") == "mandatory"
                    
                    if requires_email_verification:
                        # Crear EmailAddress para allauth
                        try:
                            from allauth.account.models import EmailAddress
                            from allauth.account import app_settings as allauth_settings
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

    new_block = '''                    # 🔥 PASO 4: VERIFICAR SI SE REQUIERE VERIFICACIÓN DE EMAIL
                    # SIEMPRE verificar la configuración de settings
                    requires_email_verification = getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", "mandatory") == "mandatory"
                    
                    # 🔥 PASO 5: CREAR EmailAddress Y ENVIAR EMAIL DE VERIFICACIÓN
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
                            
                            # Si ya existe pero está verificado, no hacer nada
                            if not email_address.verified:
                                # Enviar email de confirmación
                                send_email_confirmation(request, user, email=email)
                        except Exception as e:
                            print(f"⚠️  Error creando EmailAddress o enviando email: {e}")
                            import traceback
                            traceback.print_exc()
                    
                    # 🔥 PASO 6: SI SE REQUIERE VERIFICACIÓN, NO HACER LOGIN - REDIRIGIR A CONFIRMACIÓN
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
                            })
                    
                    # 🔥 PASO 7: SI NO SE REQUIERE VERIFICACIÓN, HACER LOGIN AUTOMÁTICO'''

    if old_block in content:
        content = content.replace(old_block, new_block)
        print("✅ Bloque de verificación de email actualizado")
    else:
        print("⚠️  No se encontró el bloque exacto, intentando reemplazo parcial...")
        
        # Intentar reemplazo más específico
        old_part = 'return redirect("account_email_verification_sent")'
        new_part = '''# Redirigir a la página de confirmación de email
                        # Usar reverse para obtener la URL correcta
                        from django.urls import reverse
                        try:
                            verification_url = reverse("account_email_verification_sent")
                            return redirect(verification_url)
                        except Exception:
                            # Si no existe la URL, renderizar el template directamente
                            return render(request, "account/email_verification_sent.html", {
                                "LANGUAGE_CODE": language_code
                            })'''
        
        if old_part in content:
            content = content.replace(old_part, new_part)
            print("✅ Redirección actualizada con fallback")
        else:
            print("❌ No se pudo encontrar el código a reemplazar")
            print("   Buscando manualmente...")
            # Buscar la línea específica
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'return redirect("account_email_verification_sent")' in line:
                    print(f"   Encontrado en línea {i+1}")
                    # Reemplazar esa línea
                    lines[i] = '''                        # Redirigir a la página de confirmación de email
                        from django.urls import reverse
                        try:
                            verification_url = reverse("account_email_verification_sent")
                            return redirect(verification_url)
                        except Exception:
                            return render(request, "account/email_verification_sent.html", {
                                "LANGUAGE_CODE": language_code
                            })'''
                    content = '\n'.join(lines)
                    print("✅ Línea reemplazada manualmente")
                    break

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Archivo actualizado")
PYEOF

# 2. Agregar URL de confirmación de email si no existe
python3 << 'PYEOF'
file_path = "gestion_taller/urls.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar si ya existe la URL
if 'account_email_verification_sent' in content:
    print("ℹ️  URL account_email_verification_sent ya existe")
else:
    # Buscar donde agregar la URL (después de signup)
    if 'path("accounts/signup/' in content:
        content = content.replace(
            'path("accounts/signup/", signup_complete, name="account_signup"),',
            'path("accounts/signup/", signup_complete, name="account_signup"),\n    # Página de confirmación de email (si allauth no la proporciona)\n    path("accounts/email/verification_sent/", TemplateView.as_view(template_name="account/email_verification_sent.html"), name="account_email_verification_sent"),'
        )
        print("✅ URL account_email_verification_sent agregada")
    else:
        print("⚠️  No se encontró el patrón para agregar la URL")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
PYEOF

echo ""
echo "✅✅✅ Cambios aplicados ✅✅✅"
echo ""
echo "📋 Resumen de correcciones:"
echo "  - Verificación explícita de ACCOUNT_EMAIL_VERIFICATION"
echo "  - Redirección a confirmación de email SIN hacer login"
echo "  - URL account_email_verification_sent agregada explícitamente"
echo "  - Fallback para renderizar template si la URL no existe"
echo "  - Mensajes de éxito en español/inglés según país"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"
echo ""
echo "🧪 Para probar:"
echo "  1. Ir a https://www.egarage.cl/accounts/signup/?from=cl"
echo "  2. Completar el formulario"
echo "  3. Debería redirigir a la página de confirmación de email"
echo "  4. NO debería hacer login automático"

