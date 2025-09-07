from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from taller.models.empresa import Empresa


class Command(BaseCommand):
    help = (
        "Elimina todas las empresas y usuarios asociados con pais=US (Estados Unidos)"
    )

    def handle(self, *args, **options):
        empresas_usa = Empresa.objects.filter(pais="US")
        total_empresas = empresas_usa.count()
        usuarios = User.objects.filter(empresa__in=empresas_usa)
        total_usuarios = usuarios.count()
        self.stdout.write(
            f"Eliminando {total_empresas} empresas y {total_usuarios} usuarios de USA..."
        )
        usuarios.delete()
        self.stdout.write(self.style.SUCCESS("Eliminación completada."))
