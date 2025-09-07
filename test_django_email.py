"""
Script para ejecutar desde la consola de Django
python manage.py shell < test_django_email.py
"""

print("=" * 50)
print("📧 PRUEBA REAL DESDE CONSOLA DJANGO")
print("=" * 50)

# Verificar configuración
from django.conf import settings

print(f"✅ EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"✅ EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"✅ EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"✅ DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

print("\n🔗 Probando conexión SMTP...")

try:
    from django.core.mail import send_mail

    # Enviar correo de prueba real
    resultado = send_mail(
        "Test de conexión SMTP - eGarage",
        "Este es un correo de prueba desde eGarage. Si recibes este mensaje, el sistema SMTP está funcionando correctamente.",
        settings.DEFAULT_FROM_EMAIL,
        ["mauricio@atlantareciclajes.cl"],  # Cambiar por tu email real
        fail_silently=False,
    )

    if resultado:
        print("✅ ¡Correo enviado exitosamente!")
        print("📱 Revisa tu bandeja de entrada (y carpeta de spam)")
        print("🎉 El sistema SMTP está conectado correctamente")
    else:
        print("❌ No se pudo enviar el correo")

except Exception as e:
    print(f"❌ Error enviando correo: {e}")
    print("🔧 Revisar configuración SMTP en settings.py")

# Probar también con EmailMultiAlternatives
print("\n📧 Probando con EmailMultiAlternatives...")

try:
    from django.core.mail import EmailMultiAlternatives

    email = EmailMultiAlternatives(
        subject="Test avanzado eGarage",
        body="Este es un test del sistema de emails avanzado de eGarage.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=["mauricio@atlantareciclajes.cl"],  # Cambiar por tu email
    )

    # Agregar contenido HTML
    html_content = """
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2 style="color: #667eea;">🚗 eGarage Email Test</h2>
        <p>Este es un <strong>correo de prueba HTML</strong> desde eGarage.</p>
        <p>Si ves este mensaje con formato, significa que:</p>
        <ul>
            <li>✅ La conexión SMTP funciona</li>
            <li>✅ Los emails HTML se procesan correctamente</li>
            <li>✅ El sistema está listo para producción</li>
        </ul>
        <p style="color: #666;">Enviado desde: {}</p>
    </body>
    </html>
    """.format(
        settings.DEFAULT_FROM_EMAIL
    )

    email.attach_alternative(html_content, "text/html")
    email.send()

    print("✅ Email HTML enviado exitosamente!")

except Exception as e:
    print(f"❌ Error con EmailMultiAlternatives: {e}")

print("\n" + "=" * 50)
print("🎯 RESULTADOS DE LA PRUEBA:")
print("Si recibiste los correos → ✅ Sistema funcionando")
print("Si no llegaron → ❌ Revisar spam o configuración")
print("=" * 50)
