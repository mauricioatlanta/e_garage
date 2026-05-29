from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from taller.models.empresa import Empresa

class Command(BaseCommand):
    help = "Purga definitivamente las empresas canceladas y sus datos en cascada tras cumplirse los 6 meses de gracia"

    def handle(self, *args, **options):
        # Calculamos el umbral de los 180 días hacia atrás
        limite_retencion = timezone.now() - timedelta(days=180)

        # Buscamos talleres inactivos cuya fecha de baja sea igual o más antigua que el límite de 6 meses
        empresas_a_purgar = Empresa.objects.filter(
            suscripcion_activa=False,
            fecha_baja__lte=limite_retencion
        )

        cantidad_purgas = empresas_a_purgar.count()

        if cantidad_purgas > 0:
            for empresa in empresas_a_purgar:
                self.stdout.write(f"Purgando permanentemente el taller ID: {empresa.id} ({empresa.nombre_taller})...")
            
            # El método delete() ejecuta un borrado en cascada eliminando automáticamente
            # todos los Clientes, Vehículos, Documentos y Usuarios vinculados a esa empresa
            empresas_a_purgar.delete()
            self.stdout.write(self.style.SUCCESS(f"Éxito: Se han eliminado {cantidad_purgas} empresas obsoletas."))
        else:
            self.stdout.write(self.style.SUCCESS("No se encontraron empresas listas para purga el día de hoy."))
