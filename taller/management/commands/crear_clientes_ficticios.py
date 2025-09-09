from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import TenantScoped
from taller.models.clientes import Cliente


class Command(BaseCommand):
    help = 'Crea 5 clientes ficticios para pruebas.'

    def handle(self, *args, **options):
        from taller.models.empresa import Empresa
        empresa = Empresa.objects.first()
        emails = [f"ficticio{i}@test.com" for i in range(1, 6)]
        for i, email in enumerate(emails, 1):
            cliente, created = Cliente.objects.get_or_create(
                empresa=empresa,
                email=email,
                defaults={
                    'nombre': f'Cliente{i}',
                    'apellido': f'Prueba{i}',
                    'telefono': f'+5690000000{i}',
                    'direccion': f'Calle Ficticia {i}',
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Cliente {email} creado'))
            else:
                self.stdout.write(self.style.WARNING(f'Cliente {email} ya existía'))
        self.stdout.write(self.style.SUCCESS('Clientes ficticios listos.'))
