"""
Views para testing del sistema de emails
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from taller.utils.email_utils import (
    enviar_correo_bienvenida,
    enviar_correo_prueba,
    verificar_conexion_smtp,
)


@login_required
def test_email_view(request):
    """Vista para probar el sistema de emails"""

    if request.method == "POST":
        email_destino = request.POST.get("email_destino")
        tipo_prueba = request.POST.get("tipo_prueba", "simple")

        if not email_destino:
            messages.error(request, "❌ Debes proporcionar un email de destino")
            return render(request, "emails/test_email.html")

        try:
            if tipo_prueba == "bienvenida":
                # Prueba de correo de bienvenida
                enlace_ficticio = request.build_absolute_uri("/activate/test123/")
                resultado = enviar_correo_bienvenida(request.user, enlace_ficticio)

                if resultado:
                    messages.success(
                        request,
                        f"✅ Correo de bienvenida enviado exitosamente a {email_destino}",
                    )
                else:
                    messages.error(
                        request,
                        f"❌ Error enviando correo de bienvenida a {email_destino}",
                    )

            else:
                # Prueba simple
                resultado = enviar_correo_prueba(
                    email_destino, request.user.first_name or request.user.username
                )

                if resultado:
                    messages.success(
                        request,
                        f"✅ Correo de prueba enviado exitosamente a {email_destino}",
                    )
                else:
                    messages.error(request, f"❌ Error enviando correo de prueba a {email_destino}")

        except Exception as e:
            messages.error(request, f"❌ Error inesperado: {str(e)}")

    return render(request, "emails/test_email.html")


@csrf_exempt
def verificar_smtp_api(request):
    """API para verificar conexión SMTP"""

    if request.method == "POST":
        resultado = verificar_conexion_smtp()
        return JsonResponse(resultado)

    return JsonResponse({"status": "error", "mensaje": "Método no permitido"})


def email_test_console():
    """
    Función para usar en la consola de Django
    Prueba la conexión de emails
    """
    print("=" * 50)
    print("🧪 PRUEBA DE CONEXIÓN SMTP - eGarage")
    print("=" * 50)

    # Verificar conexión
    resultado = verificar_conexion_smtp()
    print(f"Estado de conexión: {resultado['mensaje']}")

    if resultado["status"] == "success":
        # Enviar correo de prueba
        email_test = "support@egarage.cl"  # Cambiar por tu email
        print(f"\n📧 Enviando correo de prueba a {email_test}...")

        resultado_envio = enviar_correo_prueba(email_test, "Desarrollador")

        if resultado_envio:
            print("✅ ¡Correo enviado exitosamente!")
            print("📱 Revisa tu bandeja de entrada (y spam)")
        else:
            print("❌ Error enviando el correo")

    print("=" * 50)


# Función de prueba para la consola
def test_smtp_connection():
    """Prueba rápida de conexión SMTP desde consola Django"""
    try:
        from django.conf import settings
        from taller.utils.email_helper import get_branded_from_email, send_email_with_reply_to

        print("🔗 Probando conexión SMTP...")
        print(f"Host: {settings.EMAIL_HOST}")
        print(f"Puerto: {settings.EMAIL_PORT}")
        print(f"Usuario: {settings.EMAIL_HOST_USER}")

        resultado = send_email_with_reply_to(
            subject="Test de conexión SMTP",
            message="Este es un correo de prueba desde eGarage.",
            from_email=get_branded_from_email(settings.DEFAULT_FROM_EMAIL),
            recipient_list=["support@egarage.cl"],  # Cambiar por tu email real
            fail_silently=False,
        )

        if resultado:
            print("✅ Correo enviado exitosamente!")
            return True
        else:
            print("❌ No se pudo enviar el correo")
            return False

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False
