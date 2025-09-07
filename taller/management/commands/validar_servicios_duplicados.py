from collections import defaultdict

from django.core.management.base import BaseCommand

from taller.servicios.models import Servicio


class Command(BaseCommand):
    help = "Valida que no existan servicios ni otros servicios duplicados por país (Chile y USA)."

    def handle(self, *args, **options):
        duplicados = 0
        grupos = defaultdict(list)
        for s in Servicio.objects.all():
            clave = (s.country, s.tipo, s.code)
            grupos[clave].append(s.pk)
        for clave, ids in grupos.items():
            if len(ids) > 1:
                duplicados += len(ids) - 1
                self.stdout.write(
                    self.style.ERROR(f"Duplicados para {clave}: pks={ids}")
                )
        if duplicados == 0:
            self.stdout.write(
                self.style.SUCCESS("No hay servicios ni otros servicios duplicados.")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"Hay {duplicados} servicios duplicados.")
            )
