from django.core.management.base import BaseCommand
from taller.models import Repuesto

class Command(BaseCommand):
    help = 'Genera part_number automáticos para repuestos que no lo tienen'

    def handle(self, *args, **kwargs):
        repuestos = Repuesto.objects.filter(part_number__isnull=True) | Repuesto.objects.filter(part_number='')
        total = repuestos.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("✅ Todos los repuestos ya tienen un part_number."))
            return

        for i, repuesto in enumerate(repuestos, start=1):
            codigo = f"REP{i:03d}"
            while Repuesto.objects.filter(part_number=codigo).exists():
                i += 1
                codigo = f"REP{i:03d}"

            repuesto.part_number = codigo
            repuesto.save()
            self.stdout.write(f"🛠️  Asignado: {codigo} → {repuesto.nombre}")

        self.stdout.write(self.style.SUCCESS(f"✅ Se asignaron part_numbers a {total} repuestos."))
