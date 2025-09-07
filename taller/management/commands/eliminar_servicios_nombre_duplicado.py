from collections import defaultdict

from django.core.management.base import BaseCommand

from taller.servicios.models import ServicioName


class Command(BaseCommand):
    help = "Elimina automáticamente servicios con el mismo nombre (label) y país, aunque tengan diferente subcategoría/categoría, dejando solo uno."

    def handle(self, *args, **options):
        duplicados = defaultdict(list)
        for sn in ServicioName.objects.filter(is_default=True):
            clave = (sn.label.strip().lower(), sn.servicio.country)
            duplicados[clave].append(sn.servicio)
        eliminados = 0
        for clave, servicios in duplicados.items():
            if len(servicios) > 1:
                # Mantener el primero, eliminar el resto
                a_mantener = servicios[0]
                a_eliminar = servicios[1:]
                self.stdout.write(
                    self.style.WARNING(
                        f"Eliminando duplicados de '{clave[0]}' en país {clave[1]} (manteniendo pk={a_mantener.pk})"
                    )
                )
                for s in a_eliminar:
                    ServicioName.objects.filter(servicio=s).delete()
                    self.stdout.write(
                        f"  Eliminado servicio pk={s.pk}, subcategoria={s.subcategoria.get_label()}, categoria={s.subcategoria.categoria.get_label()} (code={s.code})"
                    )
                    s.delete()
                    eliminados += 1
        if eliminados == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "No había servicios con el mismo nombre en el mismo país para eliminar."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Eliminados {eliminados} servicios duplicados por nombre y país."
                )
            )
