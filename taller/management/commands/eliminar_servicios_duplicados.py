from collections import defaultdict

from django.core.management.base import BaseCommand

from taller.servicios.models import Servicio, ServicioName


class Command(BaseCommand):
    help = "Elimina servicios y otros servicios repetidos por país (Chile y USA) manteniendo solo uno de cada grupo."

    def handle(self, *args, **options):
        total_duplicados = 0
        detalles = []
        # Agrupar por (country, tipo, code)
        servicios = Servicio.objects.all()
        grupos = defaultdict(list)
        for s in servicios:
            clave = (s.country, s.tipo, s.code)
            grupos[clave].append(s)
        for clave, lista in grupos.items():
            if len(lista) > 1:
                # Mantener el primero, eliminar el resto
                a_mantener = lista[0]
                a_eliminar = lista[1:]
                for s in a_eliminar:
                    ServicioName.objects.filter(servicio=s).delete()
                    detalles.append(
                        f"Eliminado: id={s.id}, code={s.code}, country={s.country}, tipo={s.tipo}"
                    )
                    s.delete()
                total_duplicados += len(a_eliminar)
        self.stdout.write(
            self.style.SUCCESS(f"Eliminados {total_duplicados} servicios repetidos.")
        )
        for d in detalles:
            self.stdout.write(self.style.NOTICE(d))
