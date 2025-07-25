from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Lista todos los usuarios registrados en eGarage con sus roles y estado.'

    def handle(self, *args, **options):
        User = get_user_model()
        self.stdout.write("\nUSUARIOS REGISTRADOS EN E-GARAGE\n")
        self.stdout.write("{:<15} {:<30} {:<10} {:<10} {:<10}".format('Username', 'Email', 'Activo', 'Staff', 'Superuser'))
        self.stdout.write("-"*80)
        for user in User.objects.all():
            self.stdout.write("{:<15} {:<30} {:<10} {:<10} {:<10}".format(
                user.username, user.email, str(user.is_active), str(user.is_staff), str(user.is_superuser)
            ))
        self.stdout.write("\nPuedes resetear contraseñas con: python manage.py changepassword <username>\n")
