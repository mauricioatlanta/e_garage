from django.core.management.base import BaseCommand

from taller.models.perfil_usuario import PerfilUsuario
from taller.models.ubicacion import Ciudad


class Command(BaseCommand):
    help = "Limpia el campo ciudad en PerfilUsuario para migración a ForeignKey."

    def handle(self, *args, **options):
        count = 0
        for perfil in PerfilUsuario.objects.all():
            ciudad_val = perfil.ciudad
            if ciudad_val is None:
                continue
            try:
                ciudad_id = int(ciudad_val)
                if not Ciudad.objects.filter(pk=ciudad_id).exists():
                    perfil.ciudad = None
                    perfil.save()
                    count += 1
            except (TypeError, ValueError):
                perfil.ciudad = None
                perfil.save()
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Perfiles actualizados: {count}"))
