"""
Duplica las marcas y modelos existentes de Chile hacia México.
Útil para bootstrap inicial mientras se cargan catálogos específicos.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from taller.models.marca import Marca
from taller.models.modelo import Modelo


class Command(BaseCommand):
    help = "Copia marcas y modelos de Chile (CL) a México (MX) si no existen"

    @transaction.atomic
    def handle(self, *args, **options):
        marcas_cl = Marca.objects.filter(country="CL").order_by("nombre")
        total_marcas = marcas_cl.count()
        creadas_marcas = 0
        creados_modelos = 0

        self.stdout.write(f"[MX] Copiando {total_marcas} marcas desde Chile a México...")

        for marca in marcas_cl:
            marca_mx, created = Marca.objects.get_or_create(
                nombre=marca.nombre,
                country="MX",
                defaults={},
            )
            if created:
                creadas_marcas += 1

            modelos = Modelo.objects.filter(marca=marca).order_by("nombre")
            for modelo in modelos:
                modelo_mx, modelo_created = Modelo.objects.get_or_create(
                    nombre=modelo.nombre,
                    marca=marca_mx,
                    defaults={"country": "MX"},
                )
                if modelo_created:
                    creados_modelos += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"[MX] Marcas creadas: {creadas_marcas} | Modelos creados: {creados_modelos}"
            )
        )
