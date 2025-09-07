from collections import defaultdict

from django.core.management.base import BaseCommand

from taller.servicios.models import ServicioName


class Command(BaseCommand):
    help = "Reporta servicios con el mismo nombre (label) y país, aunque tengan diferente subcategoría/categoría."

    def handle(self, *args, **options):
        duplicados = defaultdict(list)
        for sn in ServicioName.objects.filter(is_default=True):
            clave = (sn.label.strip().lower(), sn.servicio.country)
            duplicados[clave].append(sn.servicio)
        encontrados = 0
        for clave, servicios in duplicados.items():
            if len(servicios) > 1:
                encontrados += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Nombre duplicado: '{clave[0]}' en país {clave[1]}:"
                    )
                )
                for s in servicios:
                    self.stdout.write(
                        f"  Servicio pk={s.pk}, subcategoria={s.subcategoria.get_label()}, categoria={s.subcategoria.categoria.get_label()} (code={s.code})"
                    )
        if encontrados == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "No hay servicios con el mismo nombre en el mismo país."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"Total grupos de nombres duplicados: {encontrados}")
            )
