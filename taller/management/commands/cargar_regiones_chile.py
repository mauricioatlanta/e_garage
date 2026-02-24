"""
Comando para cargar las 16 regiones de Chile en la base de datos
"""

from django.core.management.base import BaseCommand

from taller.models.region_ciudad import TallerRegion


class Command(BaseCommand):
    help = "Carga las 16 regiones de Chile en la base de datos"

    def handle(self, *args, **options):
        self.stdout.write("[CL] Cargando regiones de Chile...")

        # Lista completa de las 16 regiones de Chile
        regiones_chile = [
            "Arica y Parinacota",
            "Tarapacá",
            "Antofagasta",
            "Atacama",
            "Coquimbo",
            "Valparaíso",
            "Metropolitana de Santiago",
            "Libertador General Bernardo O'Higgins",
            "Maule",
            "Ñuble",
            "Biobío",
            "La Araucanía",
            "Los Ríos",
            "Los Lagos",
            "Aysén del General Carlos Ibáñez del Campo",
            "Magallanes y de la Antártica Chilena",
        ]

        creadas = 0
        existentes = 0

        for nombre in regiones_chile:
            obj, created = TallerRegion.objects.get_or_create(nombre=nombre)
            if created:
                self.stdout.write(self.style.SUCCESS(f"  [OK] Creada: {nombre}"))
                creadas += 1
            else:
                self.stdout.write(f"  [INFO] Existente: {nombre}")
                existentes += 1

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f"[OK] Proceso completado:\n"
                f"   - Regiones creadas: {creadas}\n"
                f"   - Regiones existentes: {existentes}\n"
                f"   - Total regiones: {TallerRegion.objects.count()}"
            )
        )
        self.stdout.write("=" * 60)

