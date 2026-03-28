"""
Comando para probar la configuración de email
"""

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = "Prueba la configuración de email y envía un correo de prueba"

    def add_arguments(self, parser):
        parser.add_argument(
            "--recipient",
            type=str,
            help="Email destinatario para el correo de prueba (default: ADMIN_EMAIL)",
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("DIAGNOSTICO DE CONFIGURACION DE EMAIL"))
        self.stdout.write("=" * 60)
        self.stdout.write("")

        # 1. Verificar configuración
        self.stdout.write(self.style.WARNING("CONFIGURACION ACTUAL:"))
        self.stdout.write(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"  EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'NO CONFIGURADO')}")
        self.stdout.write(f"  EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'NO CONFIGURADO')}")
        self.stdout.write(
            f"  EMAIL_USE_SSL: {getattr(settings, 'EMAIL_USE_SSL', 'NO CONFIGURADO')}"
        )
        self.stdout.write(
            f"  EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'NO CONFIGURADO')}"
        )
        self.stdout.write(
            f"  EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'NO CONFIGURADO')}"
        )

        email_password = getattr(settings, "EMAIL_HOST_PASSWORD", None)
        if email_password:
            self.stdout.write(
                f"  EMAIL_HOST_PASSWORD: {'*' * len(email_password)} ({len(email_password)} caracteres)"
            )
        else:
            self.stdout.write(self.style.ERROR("  EMAIL_HOST_PASSWORD: [ERROR] NO CONFIGURADO"))

        self.stdout.write(
            f"  DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'NO CONFIGURADO')}"
        )
        self.stdout.write(f"  ADMIN_EMAIL: {getattr(settings, 'ADMIN_EMAIL', 'NO CONFIGURADO')}")
        self.stdout.write(
            f"  EMAIL_TIMEOUT: {getattr(settings, 'EMAIL_TIMEOUT', 'NO CONFIGURADO')}"
        )
        self.stdout.write("")

        # 2. Verificar Allauth
        self.stdout.write(self.style.WARNING("CONFIGURACION ALLAUTH:"))
        self.stdout.write(
            f"  ACCOUNT_EMAIL_VERIFICATION: {getattr(settings, 'ACCOUNT_EMAIL_VERIFICATION', 'NO CONFIGURADO')}"
        )
        self.stdout.write(
            f"  ACCOUNT_EMAIL_REQUIRED: {getattr(settings, 'ACCOUNT_EMAIL_REQUIRED', 'NO CONFIGURADO')}"
        )
        self.stdout.write("")

        # 3. Verificar backend de Resend
        if settings.EMAIL_BACKEND == "taller.backends.resend_backend.ResendEmailBackend":
            self.stdout.write(self.style.WARNING("BACKEND DE EMAIL:"))
            self.stdout.write("  [OK] Usando ResendEmailBackend")
            self.stdout.write("")

        # 4. Intentar enviar correo de prueba
        recipient = options.get("recipient") or getattr(
            settings, "ADMIN_EMAIL", "subscription@egarage.cl"
        )

        self.stdout.write(self.style.WARNING("ENVIANDO CORREO DE PRUEBA:"))
        self.stdout.write(f"  Destinatario: {recipient}")
        self.stdout.write("")

        try:
            send_mail(
                subject="Prueba de Configuracion - eGarage",
                message="Este es un correo de prueba para verificar que la configuracion de email funciona correctamente.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS("  [OK] Correo enviado exitosamente!"))
            self.stdout.write(f"  Revisa la bandeja de entrada de {recipient}")
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write(self.style.SUCCESS("[OK] CONFIGURACION DE EMAIL OK"))
            self.stdout.write(self.style.SUCCESS("=" * 60))

        except Exception as e:
            self.stdout.write(self.style.ERROR("  [ERROR] Error enviando correo:"))
            self.stdout.write(self.style.ERROR(f"  {type(e).__name__}: {str(e)}"))
            self.stdout.write("")

            import traceback

            self.stdout.write(self.style.ERROR("  Traceback completo:"))
            self.stdout.write(self.style.ERROR("  " + "=" * 56))
            for line in traceback.format_exc().split("\n"):
                if line.strip():
                    self.stdout.write(self.style.ERROR(f"  {line}"))

            self.stdout.write("")
            self.stdout.write(self.style.ERROR("=" * 60))
            self.stdout.write(self.style.ERROR("[ERROR] CONFIGURACION DE EMAIL CON PROBLEMAS"))
            self.stdout.write(self.style.ERROR("=" * 60))
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("RECOMENDACIONES:"))
            self.stdout.write("  1. Verificar que EMAIL_PASSWORD esté configurado en .env")
            self.stdout.write("  2. Verificar credenciales del servidor SMTP")
            self.stdout.write("  3. Verificar que el servidor SMTP esté accesible")
            self.stdout.write("  4. Revisar logs del servidor para más detalles")

            import sys

            sys.exit(1)
