"""
Comando para probar el envío del correo de recuperación de contraseña.
Uso: python manage.py test_password_reset_email mauricioatlanta@gmail.com
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings


class Command(BaseCommand):
    help = "Envía un correo de recuperación de contraseña a un email (para probar SMTP/allauth)"

    def add_arguments(self, parser):
        parser.add_argument(
            "email",
            type=str,
            help="Email de la cuenta (ej: mauricioatlanta@gmail.com)",
        )

    def handle(self, *args, **options):
        email = (options["email"] or "").strip().lower()
        if not email:
            self.stdout.write(
                self.style.ERROR(
                    "Indica un email: python manage.py test_password_reset_email tu@email.com"
                )
            )
            return

        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            self.stdout.write(self.style.ERROR(f"No existe ningún usuario con email {email}"))
            return

        self.stdout.write(f"Usuario: {user.username} (id={user.pk})")
        self.stdout.write(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', '?')}")
        self.stdout.write("")

        # Usar el mismo flujo que allauth: ResetPasswordForm.save()
        from allauth.account.forms import ResetPasswordForm
        from django.http import HttpRequest

        request = HttpRequest()
        request.META["HTTP_HOST"] = getattr(settings, "ALLOWED_HOSTS", ["egarage.cl"])[0]
        request.method = "POST"
        request.user = user
        request.session = {}

        form = ResetPasswordForm(data={"email": email})
        if not form.is_valid():
            self.stdout.write(self.style.ERROR(f"Form inválido: {form.errors}"))
            return

        # form.save() envía el email vía adapter.send_mail
        try:
            form.save(request)
            self.stdout.write(
                self.style.SUCCESS(
                    "Solicitud de reset procesada (allauth envió el email si SMTP está OK)."
                )
            )
            self.stdout.write("Revisa la bandeja de entrada (y spam) de " + email)
            self.stdout.write("")
            self.stdout.write(
                "Si no llega el correo, revisa los logs del servidor (gunicorn/journalctl) por 'SMTP falló' o 'PASSWORD RESET / EMAIL'."
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            import traceback

            traceback.print_exc()
