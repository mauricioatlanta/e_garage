#!/bin/bash
# Script para corregir signup_complete para que respete la verificación de email

cd /home/atlantareciclajes/apps/egarage/current && \
source ~/.virtualenvs/venv_egarage310/bin/activate && \

echo "🔧 Corrigiendo signup_complete para respetar verificación de email..."

python3 << 'PYEOF'
file_path = "taller/views_extra/signup_complete.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Agregar import de settings si no existe
if 'from django.conf import settings' not in content:
    # Buscar la línea de imports y agregar settings
    content = content.replace(
        'from datetime import timedelta',
        'from datetime import timedelta\n\nfrom django.conf import settings'
    )
    print("✅ Import de settings agregado")

# 2. Reemplazar la sección de login automático
old_login_section = '''                    # 🔥 PASO 4: LOGIN AUTOMÁTICO
                    # Especificar backend para evitar errores de sesión
                    login(
                        request,
                        user,
                        backend="django.contrib.auth.backends.ModelBackend",
                    )

                    # Forzar guardado de la nueva sesión para evitar SessionInterrupted
                    request.session.save()

                    # 🔥 PASO 5: MENSAJE DE BIENVENIDA
                    is_spanish = pais in {"CL", "MX"}
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

                    # 🔥 PASO 6: REDIRIGIR SEGÚN PAÍS Y PLAN
                    if plan == "trial":
                        # Trial: acceso inmediato al dashboard
                        if pais == "CL":
                            return redirect("/cl/es/dashboard/")
                        elif pais == "MX":
                            return redirect("/mx/es/dashboard/")
                        else:
                            return redirect("/us/en/dashboard/")
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
                            )'''

new_login_section = '''                    # 🔥 PASO 4: CREAR EmailAddress Y ENVIAR EMAIL DE VERIFICACIÓN (si se requiere)
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
                            )'''

if old_login_section in content:
    content = content.replace(old_login_section, new_login_section)
    print("✅ Sección de login actualizada")
else:
    print("⚠️  No se encontró la sección exacta (puede que ya esté actualizada)")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Archivo actualizado")
PYEOF

echo ""
echo "✅✅✅ Cambios aplicados ✅✅✅"
echo ""
echo "📋 Resumen de cambios:"
echo "  - signup_complete ahora verifica ACCOUNT_EMAIL_VERIFICATION"
echo "  - Si es 'mandatory', NO hace login automático"
echo "  - Redirige a account_email_verification_sent"
echo "  - Crea EmailAddress para allauth"
echo ""
echo "🔄 Reiniciando servidor..."
touch /home/atlantareciclajes/apps/egarage/current/gestion_taller/wsgi.py && \
echo "✅ Servidor reiniciado"

