#!/usr/bin/env python
"""
Test de correo electrónico desde Django
Este script prueba el sistema de emails usando Django
"""

import os
import sys

import django

# Configurar Django ANTES de importar settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "e_garage.settings")
django.setup()

from django.conf import settings
from django.core.mail import send_mail

print("=" * 50)
print("📧 PRUEBA REAL DESDE CONSOLA DJANGO")
print("=" * 50)

print(f"✅ EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"✅ EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"✅ EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"✅ EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")

print("\n🚀 Enviando email de prueba...")

try:
    resultado = send_mail(
        subject="Test de conexión SMTP - eGarage Django",
        message="Este es un correo de prueba enviado desde Django. El sistema de emails está funcionando correctamente.",
        from_email="eGarage <contacto@atlantareciclajes.cl>",
        recipient_list=["mauricio@atlantareciclajes.cl"],
        fail_silently=False,
    )

    if resultado:
        print("✅ ¡Correo enviado exitosamente desde Django!")
        print("📱 Revisa tu bandeja de entrada (y spam)")
        print(f"📊 Número de emails enviados: {resultado}")
    else:
        print("❌ No se pudo enviar el correo")

except Exception as e:
    print(f"❌ Error al enviar correo: {e}")
    print(f"❌ Tipo de error: {type(e).__name__}")

print("\n🎉 Prueba de Django completada!")
