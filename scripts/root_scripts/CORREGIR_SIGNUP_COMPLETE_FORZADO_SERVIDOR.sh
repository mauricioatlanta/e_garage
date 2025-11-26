#!/bin/bash
# Script para FORZAR la corrección de signup_complete en el servidor
# Verifica configuración y aplica cambios de forma robusta

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔍 Verificando configuración actual..."

# Verificar ACCOUNT_EMAIL_VERIFICATION
python3 << 'PYEOF'
import os
import sys
import django

sys.path.insert(0, os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.conf import settings

email_verification = getattr(settings, 'ACCOUNT_EMAIL_VERIFICATION', 'none')
print(f"📋 ACCOUNT_EMAIL_VERIFICATION actual: {email_verification}")

if email_verification != 'mandatory':
    print("⚠️  ADVERTENCIA: ACCOUNT_EMAIL_VERIFICATION no está configurado como 'mandatory'")
    print("   Esto puede causar que el login automático ocurra sin verificación")
else:
    print("✅ ACCOUNT_EMAIL_VERIFICATION está configurado correctamente como 'mandatory'")
PYEOF

echo ""
echo "🔧 Aplicando correcciones en signup_complete.py..."

python3 << 'PYEOF'
import re

file_path = "taller/views_extra/signup_complete.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Verificar si ya tiene el import de settings
if 'from django.conf import settings' not in content:
    # Agregar import después de los otros imports
    content = content.replace(
        'from django.utils.translation import activate',
        'from django.utils.translation import activate\n\nfrom django.conf import settings'
    )
    print("✅ Import de settings agregado")

# Buscar la sección problemática - puede estar en diferentes formatos
# Patrón 1: Buscar "PASO 4: LOGIN AUTOMÁTICO" o similar
patterns_to_replace = [
    # Patrón completo con login automático
    (r'# 🔥 PASO 4: LOGIN AUTOMÁTICO.*?# 🔥 PASO 6: REDIRIGIR SEGÚN PAÍS Y PLAN.*?return redirect\([^)]+\)', 
     '''# 🔥 PASO 4: CREAR EmailAddress Y ENVIAR EMAIL DE VERIFICACIÓN (si se requiere)
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
                    # 🔥 PASO 6: LOGIN AUTOMÁTICO
                    login(
                        request,
                        user,
                        backend="django.contrib.auth.backends.ModelBackend",
                    )

                    # Forzar guardado de la nueva sesión para evitar SessionInterrupted
                    request.session.save()

                    # 🔥 PASO 7: MENSAJE DE BIENVENIDA
                    is_spanish = pais in {"CL", "MX", "CO", "PE", "VE", "EC"}
                    if plan == "trial":
                        messages.success(
                            request,
                            (
                                f"¡Bienvenido {nombre}! Tu prueba gratuita de 30 días ha comenzado."
                                if is_spanish
                                else f"Welcome {nombre}! Your 30-day free trial has started."
                            ),
                        )
                    else:
                        messages.info(
                            request,
                            (
                                f"Cuenta creada. Completa el pago para activar tu plan {plan}."
                                if is_spanish
                                else f"Account created. Complete your payment to activate the {plan} plan."
                            ),
                        )

                    # 🔥 PASO 8: REDIRIGIR SEGÚN PAÍS Y PLAN
                    if plan == "trial":
                        # Trial: acceso inmediato al dashboard
                        if pais == "CL":
                            return redirect("/cl/es/centro-operaciones/")
                        elif pais == "MX":
                            return redirect("/mx/es/centro-operaciones/")
                        else:
                            return redirect("/us/en/centro-operaciones-espacial/")
                    else:
                        # Planes pagados: a página de pago
                        if pais == "CL":
                            return redirect(
                                f"/cl/es/suscripcion/pago/?plan={plan}&amount={valor_mensual}"
                            )
                        elif pais == "MX":
                            return redirect(
                                f"/mx/es/suscripcion/pago/?plan={plan}&amount={valor_mensual}"
                            )
                        else:
                            return redirect(
                                f"/us/en/subscription/payment/?plan={plan}&amount={valor_mensual}"
                            )''', re.DOTALL),
]

# Buscar si ya tiene la verificación de email
has_email_verification = 'requires_email_verification' in content and 'account_email_verification_sent' in content

if not has_email_verification:
    # Buscar el punto exacto donde insertar - después de crear la empresa
    empresa_created_pattern = r'(suscripcion_activa=config\["suscripcion_activa"\],\s*\)\s*)'
    
    replacement_code = '''                    )

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
                    # 🔥 PASO 6: LOGIN AUTOMÁTICO
                    login(
                        request,
                        user,
                        backend="django.contrib.auth.backends.ModelBackend",
                    )

                    # Forzar guardado de la nueva sesión para evitar SessionInterrupted
                    request.session.save()

                    # 🔥 PASO 7: MENSAJE DE BIENVENIDA
                    is_spanish = pais in {"CL", "MX", "CO", "PE", "VE", "EC"}
                    if plan == "trial":
                        messages.success(
                            request,
                            (
                                f"¡Bienvenido {nombre}! Tu prueba gratuita de 30 días ha comenzado."
                                if is_spanish
                                else f"Welcome {nombre}! Your 30-day free trial has started."
                            ),
                        )
                    else:
                        messages.info(
                            request,
                            (
                                f"Cuenta creada. Completa el pago para activar tu plan {plan}."
                                if is_spanish
                                else f"Account created. Complete your payment to activate the {plan} plan."
                            ),
                        )

                    # 🔥 PASO 8: REDIRIGIR SEGÚN PAÍS Y PLAN
                    if plan == "trial":
                        # Trial: acceso inmediato al dashboard
                        if pais == "CL":
                            return redirect("/cl/es/centro-operaciones/")
                        elif pais == "MX":
                            return redirect("/mx/es/centro-operaciones/")
                        else:
                            return redirect("/us/en/centro-operaciones-espacial/")
                    else:
                        # Planes pagados: a página de pago
                        if pais == "CL":
                            return redirect(
                                f"/cl/es/suscripcion/pago/?plan={plan}&amount={valor_mensual}"
                            )
                        elif pais == "MX":
                            return redirect(
                                f"/mx/es/suscripcion/pago/?plan={plan}&amount={valor_mensual}"
                            )
                        else:
                            return redirect(
                                f"/us/en/subscription/payment/?plan={plan}&amount={valor_mensual}"
                            )
'''
    
    # Buscar el patrón y reemplazar
    match = re.search(empresa_created_pattern, content)
    if match:
        # Encontrar dónde está el login automático después
        login_pattern = r'(# 🔥 PASO 4: LOGIN AUTOMÁTICO.*?return redirect\([^)]+\))'
        login_match = re.search(login_pattern, content, re.DOTALL)
        
        if login_match:
            # Reemplazar desde después de crear empresa hasta antes del login
            old_section = match.group(1) + login_match.group(1)
            new_section = replacement_code
            content = content.replace(old_section, new_section)
            print("✅ Sección de login reemplazada correctamente")
        else:
            # Insertar después de crear empresa
            content = content.replace(match.group(1), replacement_code, 1)
            print("✅ Código de verificación de email insertado")
    else:
        print("⚠️  No se encontró el patrón exacto, intentando búsqueda más amplia...")
        # Buscar cualquier lugar después de crear empresa
        if 'suscripcion_activa=config["suscripcion_activa"]' in content:
            # Insertar justo después
            insert_point = content.find('suscripcion_activa=config["suscripcion_activa"]')
            if insert_point != -1:
                # Encontrar el cierre del paréntesis
                close_paren = content.find(')', insert_point)
                if close_paren != -1:
                    # Insertar después del cierre
                    content = content[:close_paren+1] + replacement_code + content[close_paren+1:]
                    print("✅ Código insertado después de crear empresa")
                else:
                    print("❌ No se encontró el cierre del paréntesis")
            else:
                print("❌ No se encontró el punto de inserción")
else:
    print("✅ El código ya tiene la verificación de email implementada")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Archivo actualizado")
PYEOF

echo ""
echo "✅✅✅ Correcciones aplicadas ✅✅✅"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"
echo ""
echo "📋 Próximos pasos:"
echo "  1. Prueba registrarte nuevamente"
echo "  2. Deberías ser redirigido a la página de confirmación de email"
echo "  3. NO deberías hacer login automático"



