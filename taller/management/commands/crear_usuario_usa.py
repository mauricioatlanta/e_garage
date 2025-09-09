from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Crea el usuario de prueba testuser_usa para USA Garage.'

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(username='testuser_usa').exists():
            User.objects.create_user(
                username='testuser_usa',
                email='testuser@usa-garage.com',
                password='TestUSA2025!',
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS('Usuario testuser_usa creado.'))
        else:
            self.stdout.write(self.style.WARNING('El usuario testuser_usa ya existe.'))
