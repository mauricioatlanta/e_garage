from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Lista todos los usuarios registrados en eGarage con sus roles y estado."

    def handle(self, *args, **options):
        User = get_user_model()
        self.stdout.write("\nUSUARIOS REGISTRADOS EN E-GARAGE\n")
        self.stdout.write(
            "{:<15} {:<30} {:<10} {:<10} {:<10}".format(
                "Username", "Email", "Activo", "Staff", "Superuser"
            )
        )
        self.stdout.write("-" * 80)
        for user in User.objects.all():
            self.stdout.write(
                f"{user.username:<15} {user.email:<30} {str(user.is_active):<10} {str(user.is_staff):<10} {str(user.is_superuser):<10}"
            )
        self.stdout.write(
            "\nPuedes resetear contraseñas con: python manage.py changepassword <username>\n"
        )
