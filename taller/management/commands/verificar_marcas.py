"""
Management command para verificar el estado de las marcas en la base de datos.
"""

from django.core.management.base import BaseCommand
from django.db.models import Count

from taller.models.marca import Marca


class Command(BaseCommand):
    help = "Verifica el estado de las marcas en la base de datos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--country",
            type=str,
            help="Filtrar por país específico (gl, CL, US, MX, etc.)",
        )
        parser.add_argument(
            "--detail",
            action="store_true",
            help="Mostrar lista detallada de marcas",
        )

    def handle(self, *args, **options):
        country_filter = options.get("country")
        show_detail = options.get("detail", False)

        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("VERIFICACION DE MARCAS EN LA BASE DE DATOS"))
        self.stdout.write("=" * 80)

        # Estadísticas por país
        if country_filter:
            qs = Marca.objects.filter(country=country_filter.upper() if country_filter.upper() != "GL" else "gl")
            self.stdout.write(f"\nFiltrando por pais: {country_filter}")
        else:
            qs = Marca.objects.all()

        # Agrupar por país
        stats = qs.values("country").annotate(total=Count("id")).order_by("country")

        self.stdout.write("\nESTADISTICAS POR PAIS:")
        self.stdout.write("-" * 80)
        total_general = 0
        for stat in stats:
            country = stat["country"]
            count = stat["total"]
            total_general += count
            country_label = dict(Marca._meta.get_field("country").choices).get(
                country, country
            )
            self.stdout.write(f"   {country_label:20} ({country:3}): {count:4} marcas")

        self.stdout.write("-" * 80)
        self.stdout.write(f"   {'TOTAL':20}      : {total_general:4} marcas")

        # Mostrar detalle si se solicita
        if show_detail:
            self.stdout.write("\nDETALLE DE MARCAS:")
            self.stdout.write("-" * 80)
            for stat in stats:
                country = stat["country"]
                country_label = dict(Marca._meta.get_field("country").choices).get(
                    country, country
                )
                self.stdout.write(f"\n   {country_label} ({country}):")
                marcas = Marca.objects.filter(country=country).order_by("nombre")
                for marca in marcas:
                    self.stdout.write(f"      - {marca.nombre} (ID: {marca.id})")

        # Verificar marcas globales
        marcas_globales = Marca.objects.filter(country="gl").count()
        self.stdout.write("\n" + "=" * 80)
        if marcas_globales > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"[OK] Sistema configurado correctamente: {marcas_globales} marcas globales disponibles"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    "[WARNING] No se encontraron marcas globales. Ejecuta: python manage.py seed_marcas"
                )
            )

        self.stdout.write("=" * 80)

