#!/usr/bin/env python
"""
Test simplificado de email - Solo configuración SMTP
Este script prueba solo la funcionalidad de emails sin Django completo
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Configuración SMTP (copiada de settings.py)
EMAIL_HOST = "mail.atlantareciclajes.cl"
EMAIL_PORT = 465
EMAIL_HOST_USER = "contacto@atlantareciclajes.cl"
EMAIL_HOST_PASSWORD = ""  # Pega aquí la contraseña correcta del correo
EMAIL_USE_SSL = True

print("=" * 60)
print("📧 PRUEBA FINAL DE EMAIL SMTP - eGarage")
print("=" * 60)

print(f"🔧 Configuración:")
print(f"   Host: {EMAIL_HOST}")
print(f"   Puerto: {EMAIL_PORT}")
print(f"   Usuario: {EMAIL_HOST_USER}")
print(f"   SSL: {EMAIL_USE_SSL}")

print("\n🚀 Conectando al servidor SMTP...")

try:
    # Crear conexión SMTP
    if EMAIL_USE_SSL:
        server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT)
    else:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()

    # Autenticar
    server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
    print("✅ ¡Conexión y autenticación exitosa!")

    # Crear mensaje de prueba
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Prueba Final SMTP - eGarage Sistema"
    msg["From"] = f"eGarage Sistema <{EMAIL_HOST_USER}>"
    msg["To"] = "mauricio@atlantareciclajes.cl"

    # Texto plano
    texto_plano = """
¡Hola Mauricio!

Este es un correo de prueba del sistema eGarage.

✅ El sistema de emails está funcionando perfectamente
🚀 La configuración SMTP está correcta
📧 Los correos se envían desde: contacto@atlantareciclajes.cl

¡El sistema está listo para usar!

Saludos,
eGarage - Sistema de Gestión de Talleres
    """

    # HTML
    html = """
    <html>
    <head></head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #0066cc;">🚗 eGarage - Prueba Final del Sistema</h2>
            
            <p>¡Hola <strong>Mauricio</strong>!</p>
            
            <p>Este es un correo de prueba del sistema <strong>eGarage</strong>.</p>
            
            <div style="background-color: #f0f8ff; padding: 15px; border-left: 4px solid #0066cc; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #0066cc;">Estado del Sistema:</h3>
                <ul style="list-style: none; padding: 0;">
                    <li>✅ El sistema de emails está funcionando perfectamente</li>
                    <li>🚀 La configuración SMTP está correcta</li>
                    <li>📧 Los correos se envían desde: contacto@atlantareciclajes.cl</li>
                    <li>🎉 ¡El sistema está listo para usar!</li>
                </ul>
            </div>
            
            <p style="margin-top: 30px;">
                <strong>eGarage</strong><br>
                <em>Sistema de Gestión de Talleres</em><br>
                <small style="color: #666;">Configurado y funcionando correctamente</small>
            </p>
        </div>
    </body>
    </html>
    """

    # Adjuntar partes
    part1 = MIMEText(texto_plano, "plain", "utf-8")
    part2 = MIMEText(html, "html", "utf-8")

    msg.attach(part1)
    msg.attach(part2)

    # Enviar email
    print("📤 Enviando email de prueba final...")
    server.send_message(msg)
    print("✅ ¡Email enviado exitosamente!")

    # Cerrar conexión
    server.quit()
    print("🔐 Conexión cerrada correctamente")

    print("\n" + "=" * 60)
    print("🎉 ¡PRUEBA COMPLETADA CON ÉXITO!")
    print("📱 Revisa tu bandeja de entrada en mauricio@atlantareciclajes.cl")
    print("📧 El sistema de emails de eGarage está listo para usar")
    print("=" * 60)

except Exception as e:
    print(f"❌ Error: {e}")
    print(f"❌ Tipo de error: {type(e).__name__}")
    print("\n🔧 Verifica:")
    print("   - Credenciales SMTP")
    print("   - Conexión a internet")
    print("   - Configuración del servidor")
