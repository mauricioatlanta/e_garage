#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script de pruebas: correo, teléfono, WhatsApp y signup (smoke test)."""
import os
import sys

# Evitar UnicodeEncodeError en consola Windows (emojis en WhatsApp)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

import django

django.setup()

from django.conf import settings
from django.core.mail import send_mail
from urllib.parse import quote

# ========== 1. Test: correo y teléfono configurados ==========
print("=" * 50)
print("1. EMAIL / TELÉFONO CONFIGURADOS")
print("=" * 50)

print("\n=== EMAIL / SOPORTE eGarage ===")
print("DEFAULT_FROM_EMAIL:", getattr(settings, "DEFAULT_FROM_EMAIL", None))
print("SERVER_EMAIL:", getattr(settings, "SERVER_EMAIL", None))
print("EGARAGE_SUPPORT_EMAIL:", getattr(settings, "EGARAGE_SUPPORT_EMAIL", None))

print("\n=== WHATSAPP / TELÉFONO SOPORTE ===")
print("EGARAGE_SUPPORT_PHONE:", getattr(settings, "EGARAGE_SUPPORT_PHONE", None))
print("EGARAGE_WHATSAPP_NUMBER:", getattr(settings, "EGARAGE_WHATSAPP_NUMBER", None))

print("\n=== .env comprobación mínima (nombres EGARAGE_*) ===")
for key in [
    "EGARAGE_SUPPORT_EMAIL",
    "EGARAGE_SUPPORT_PHONE",
    "EGARAGE_WHATSAPP_NUMBER",
]:
    val = getattr(settings, key, None)
    print(f"{key} =", val if val is not None else "NO DEFINIDO EN settings")

# Variables de soporte que SÍ usa el proyecto (por si las quieres usar como referencia)
print("\n=== Variables de soporte usadas en el proyecto ===")
for key in [
    "SUPPORT_EMAIL",
    "SUPPORT_WHATSAPP_E164",
    "SUPPORT_WHATSAPP_DISPLAY",
    "SUPPORT_WHATSAPP_WA_ME",
]:
    val = getattr(settings, key, None)
    print(f"{key} =", val)

# ========== 2. Enviar correo ficticio de registro ==========
print("\n" + "=" * 50)
print("2. ENVÍO CORREO DE PRUEBA")
print("=" * 50)

destino = "mauricioatlanta@gmail.com"
login_url = "https://www.egarage.cl/cl/es/accounts/login/"
subject = "[eGarage] Bienvenido, tu cuenta está casi lista 🚀"
message = (
    "Hola Mauricio!\n\n"
    "Este es un correo de PRUEBA para verificar la configuración de correo de eGarage.\n\n"
    "Simulamos que acabas de registrar tu cuenta en eGarage.\n"
    f"Para iniciar sesión, usa este enlace de login:\n{login_url}\n\n"
    "Si tú no solicitaste este registro, puedes ignorar este mensaje.\n\n"
    "Atentamente,\n"
    "Equipo eGarage"
)
from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@egarage.cl")

print("Enviando email de PRUEBA a:", destino)
print("FROM:", from_email)

try:
    send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=[destino],
        fail_silently=False,
    )
    print("OK: Django no lanzó excepción al intentar enviar el correo.")
    print("Si EMAIL_BACKEND es console, el contenido salió en consola.")
    print("Si ya tienes SMTP, revisa la bandeja de entrada de", destino)
except Exception as e:
    print("ERROR al enviar:", type(e).__name__, str(e))

# ========== 3. Mensaje ficticio WhatsApp (extensión plan 30 días) ==========
print("\n" + "=" * 50)
print("3. MENSAJE FICTICIO WHATSAPP (extensión plan 30 días)")
print("=" * 50)

numero_wa = "+569 6360 7348"
texto = (
    "Hola Mauricio 👋\n\n"
    "Te avisamos desde eGarage que tu plan ha sido EXTENDIDO por 30 días adicionales, "
    "sin costo, como parte de nuestro programa de soporte prioritario.\n\n"
    "No necesitas hacer nada, tu cuenta seguirá activa normalmente.\n\n"
    "Cualquier duda, respóndenos por este mismo canal.\n\n"
    "Equipo eGarage 🚗✨"
)

numero_limpio = numero_wa.replace(" ", "").replace("+", "")
wa_url = f"https://wa.me/{numero_limpio}?text={quote(texto)}"

print("Número:", numero_wa)
print("\nTexto a enviar:")
print(texto)
print("\nURL wa.me para probar en navegador:")
print(wa_url)

# ========== 4. Smoke test: signup ==========
print("\n" + "=" * 50)
print("4. SMOKE TEST: /cl/es/accounts/signup/")
print("=" * 50)

from django.test import Client

c = Client()
r = c.get("/cl/es/accounts/signup/")
print("GET /cl/es/accounts/signup/ ->", r.status_code)

if r.status_code == 200:
    print("OK: la vista de registro responde 200 (formulario se carga).")
else:
    print("OJO: código distinto de 200, revisar redirecciones o errores.")

print("\n" + "=" * 50)
print("Pruebas completadas.")
print("=" * 50)
