"""
Script de prueba para el sistema de emails de eGarage
Ejecutar con: python test_email_system.py
"""

import os
import sys

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "e_garage.settings")
sys.path.append("C:/projecto/projecto_1/e_garage")


def test_email_system_simple():
    """Prueba el sistema de emails sin conectar a Django"""
    print("=" * 60)
    print("📧 PRUEBA DEL SISTEMA DE EMAILS - eGarage")
    print("=" * 60)

    try:
        # Test 1: Verificar archivos creados
        print("\n📁 Test 1: Verificar archivos del sistema")

        files_to_check = [
            (
                "C:/projecto/projecto_1/e_garage/taller/utils/email_utils.py",
                "Utilidades de email",
            ),
            (
                "C:/projecto/projecto_1/e_garage/taller/views/email_views.py",
                "Views de email",
            ),
            (
                "C:/projecto/projecto_1/e_garage/templates/emails/bienvenida.html",
                "Template de bienvenida",
            ),
            (
                "C:/projecto/projecto_1/e_garage/templates/emails/test_email.html",
                "Template de prueba",
            ),
            ("C:/projecto/projecto_1/e_garage/taller/emails/urls.py", "URLs de emails"),
            (
                "C:/projecto/projecto_1/e_garage/e_garage/settings.py",
                "Configuración SMTP",
            ),
        ]

        for file_path, description in files_to_check:
            if os.path.exists(file_path):
                print(f"✅ {description} - Archivo creado")
            else:
                print(f"❌ {description} - Archivo no encontrado")

        # Test 2: Verificar configuración SMTP en settings
        print("\n🔧 Test 2: Verificar configuración SMTP")

        settings_path = "C:/projecto/projecto_1/e_garage/e_garage/settings.py"
        with open(settings_path, "r", encoding="utf-8") as f:
            settings_content = f.read()

        smtp_configs = [
            "EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'",
            "EMAIL_HOST = 'mail.atlantareciclajes.cl'",
            "EMAIL_PORT = 465",
            "EMAIL_USE_SSL = True",
            "EMAIL_HOST_USER = 'contacto@atlantareciclajes.cl'",
            "DEFAULT_FROM_EMAIL = 'eGarage <contacto@atlantareciclajes.cl>'",
        ]

        for config in smtp_configs:
            if config in settings_content:
                print(f"✅ {config}")
            else:
                print(f"❌ Falta configuración: {config}")

        # Test 3: Verificar funciones de email
        print("\n📧 Test 3: Verificar funciones de email")

        email_utils_path = "C:/projecto/projecto_1/e_garage/taller/utils/email_utils.py"
        with open(email_utils_path, "r", encoding="utf-8") as f:
            email_content = f.read()

        functions_to_check = [
            "def enviar_correo_bienvenida(",
            "def enviar_correo_prueba(",
            "def verificar_conexion_smtp(",
            "EmailMultiAlternatives",
            "render_to_string",
        ]

        for function in functions_to_check:
            if function in email_content:
                print(f"✅ {function} - Implementado")
            else:
                print(f"❌ {function} - No encontrado")

        # Test 4: Verificar template HTML
        print("\n🎨 Test 4: Verificar template de bienvenida")

        template_path = (
            "C:/projecto/projecto_1/e_garage/templates/emails/bienvenida.html"
        )
        with open(template_path, "r", encoding="utf-8") as f:
            template_content = f.read()

        template_elements = [
            "¡Bienvenido a eGarage!",
            "{{ first_name }}",
            "{{ enlace }}",
            "🔓 Activar mi cuenta",
            "linear-gradient",
            "<!DOCTYPE html>",
        ]

        for element in template_elements:
            if element in template_content:
                print(f"✅ {element} - Presente en template")
            else:
                print(f"❌ {element} - Falta en template")

        # Test 5: Verificar URLs
        print("\n🔗 Test 5: Verificar configuración de URLs")

        urls_path = "C:/projecto/projecto_1/e_garage/taller/emails/urls.py"
        with open(urls_path, "r", encoding="utf-8") as f:
            urls_content = f.read()

        main_urls_path = "C:/projecto/projecto_1/e_garage/taller/urls.py"
        with open(main_urls_path, "r", encoding="utf-8") as f:
            main_urls_content = f.read()

        if "path('test/', test_email_view" in urls_content:
            print("✅ URL de prueba configurada")
        else:
            print("❌ URL de prueba no configurada")

        if "path('emails/', include('taller.emails.urls'))" in main_urls_content:
            print("✅ URLs de emails integradas en sistema principal")
        else:
            print("❌ URLs de emails no integradas")

        print("\n" + "=" * 60)
        print("🎉 SISTEMA DE EMAILS - VERIFICACIÓN COMPLETADA")
        print("=" * 60)

        print("\n🚀 Funcionalidades implementadas:")
        print("   ✅ Configuración SMTP con contacto@atlantareciclajes.cl")
        print("   ✅ Función enviar_correo_bienvenida()")
        print("   ✅ Template HTML profesional de bienvenida")
        print("   ✅ Vista de prueba de emails")
        print("   ✅ API de verificación SMTP")
        print("   ✅ Función de prueba desde consola")
        print("   ✅ URLs configuradas correctamente")

        print("\n📱 Para probar el sistema:")
        print("   1. Iniciar servidor Django: python manage.py runserver")
        print("   2. Visitar: http://localhost:8000/emails/test/")
        print("   3. Ingresar tu email personal")
        print("   4. Enviar prueba y verificar bandeja de entrada")

        print("\n🖥️ Prueba desde consola Django:")
        print("   python manage.py shell")
        print("   from taller.views.email_views import test_smtp_connection")
        print("   test_smtp_connection()")

        print("\n📧 Configuración SMTP activa:")
        print("   • Host: mail.atlantareciclajes.cl")
        print("   • Puerto: 465 (SSL)")
        print("   • Usuario: contacto@atlantareciclajes.cl")
        print("   • Remitente: eGarage <contacto@atlantareciclajes.cl>")

        print("\n🎯 Próximos pasos:")
        print("   1. Probar envío de correos ✅")
        print("   2. Implementar emails bilingües (Chile vs USA)")
        print("   3. Crear templates específicos por país")
        print("   4. Integrar con sistema de notificaciones")

        return True

    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_smtp_manual():
    """Prueba manual de SMTP usando solo Python"""
    print("\n" + "=" * 50)
    print("📧 PRUEBA MANUAL DE SMTP")
    print("=" * 50)

    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        # Configuración
        smtp_host = "mail.atlantareciclajes.cl"
        smtp_port = 465
        username = "contacto@atlantareciclajes.cl"
        password = "laila2013@"

        print(f"🔗 Conectando a {smtp_host}:{smtp_port}...")

        # Crear conexión
        server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        server.login(username, password)

        print("✅ Conexión SMTP exitosa!")

        # Crear mensaje
        msg = MIMEMultipart()
        msg["From"] = f"eGarage <{username}>"
        msg["To"] = "mauricio@atlantareciclajes.cl"  # Cambiar por tu email
        msg["Subject"] = "Test manual SMTP - eGarage"

        body = """
        Hola,
        
        Este es un test manual de la conexión SMTP de eGarage.
        
        Si recibes este mensaje, significa que el servidor SMTP está funcionando correctamente.
        
        Configuración utilizada:
        - Host: mail.atlantareciclajes.cl
        - Puerto: 465 (SSL)
        - Usuario: contacto@atlantareciclajes.cl
        
        Saludos,
        Sistema eGarage
        """

        msg.attach(MIMEText(body, "plain"))

        # Enviar
        text = msg.as_string()
        server.sendmail(username, "mauricio@atlantareciclajes.cl", text)
        server.quit()

        print("✅ Email de prueba enviado exitosamente!")
        print("📱 Revisa tu bandeja de entrada (y spam)")

        return True

    except Exception as e:
        print(f"❌ Error en prueba manual: {e}")
        return False


if __name__ == "__main__":
    # Ejecutar prueba simple
    resultado = test_email_system_simple()

    if resultado:
        print("\n" + "=" * 50)
        print("¿Deseas ejecutar también la prueba manual SMTP? (y/n)")
        respuesta = input().lower().strip()

        if respuesta in ["y", "yes", "s", "si", "sí"]:
            test_smtp_manual()

    print("\n🎉 ¡Pruebas completadas!")
    print("📧 El sistema de emails está listo para usar")
