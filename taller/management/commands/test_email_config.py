"""
Comando para probar la configuración de email
"""

from django.conf import settings
from django.core.management.base import BaseCommand
from taller.utils.email_helper import get_branded_from_email, get_support_reply_to, send_email_with_reply_to


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
        self.stdout.write(
            f"  DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'NO CONFIGURADO')}"
        )
        self.stdout.write(f"  SERVER_EMAIL: {getattr(settings, 'SERVER_EMAIL', 'NO CONFIGURADO')}")
        self.stdout.write(
            f"  SUPPORT_EMAIL: {getattr(settings, 'SUPPORT_EMAIL', 'NO CONFIGURADO')}"
        )
        self.stdout.write(
            f"  EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'NO CONFIGURADO')}"
        )
        self.stdout.write(f"  ADMIN_EMAIL: {getattr(settings, 'ADMIN_EMAIL', 'NO CONFIGURADO')}")
        self.stdout.write(
            f"  EMAIL_TIMEOUT: {getattr(settings, 'EMAIL_TIMEOUT', 'NO CONFIGURADO')}"
        )
        resend_api_key = (
            getattr(settings, "RESEND_API_KEY", "")
            or getattr(settings, "ANYMAIL", {}).get("RESEND_API_KEY", "")
            or ""
        )
        if resend_api_key:
            self.stdout.write(
                f"  RESEND_API_KEY: {'*' * max(len(resend_api_key) - 4, 0)}{resend_api_key[-4:]}"
            )
        else:
            self.stdout.write(self.style.ERROR("  RESEND_API_KEY: [ERROR] NO CONFIGURADO"))
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
        if settings.EMAIL_BACKEND == "anymail.backends.resend.EmailBackend":
            self.stdout.write(self.style.WARNING("BACKEND DE EMAIL:"))
            self.stdout.write("  [OK] Usando anymail.backends.resend.EmailBackend")
            self.stdout.write("")

        # 4. Intentar enviar correo de prueba
        recipient = options.get("recipient") or getattr(settings, "ADMIN_EMAIL", None) or get_support_reply_to()

        self.stdout.write(self.style.WARNING("ENVIANDO CORREO DE PRUEBA:"))
        self.stdout.write(f"  Destinatario: {recipient}")
        self.stdout.write("")

        try:
            send_email_with_reply_to(
                subject="Prueba de Configuracion - eGarage",
                message="Este es un correo de prueba para verificar que la configuracion de email funciona correctamente.",
                from_email=get_branded_from_email(settings.DEFAULT_FROM_EMAIL),
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
            self.stdout.write("  1. Verificar que RESEND_API_KEY esté configurada en .env/.env.prod")
            self.stdout.write("  2. Confirmar que django-anymail esté instalado")
            self.stdout.write(
                f"  3. Confirmar que {get_support_reply_to()} esté verificado en Resend"
            )
            self.stdout.write("  4. Revisar logs del servidor para más detalles")

            import sys

            sys.exit(1)
