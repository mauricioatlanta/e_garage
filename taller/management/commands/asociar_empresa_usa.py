from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from taller.models.empresa import Empresa

class Command(BaseCommand):
    help = 'Crea la empresa USA y la asocia al usuario testuser_usa.'

    def handle(self, *args, **options):
        user = User.objects.filter(username='testuser_usa').first()
        if not user:
            self.stdout.write(self.style.ERROR('El usuario testuser_usa no existe.'))
            return
        empresa, created = Empresa.objects.get_or_create(
            user=user,
            defaults={
                'nombre_taller': 'USA Test Garage',
                'empresa': 'USA Test Garage',
                'pais': 'US',
                'email': 'testuser@usa-garage.com',
                'telefono': '+1-404-404-4040',
                'direccion': 'Main St 1990',
                'zona_horaria': 'America/New_York',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Empresa USA creada y asociada a {user.username}.'))
        else:
            self.stdout.write(self.style.WARNING(f'La empresa USA ya existía para {user.username}.'))
