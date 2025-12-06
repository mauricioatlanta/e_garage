"""
Comando de gestión para exportar marcas de Chile a JSON
Ejecutar: python manage.py export_marcas_chile --file data/marcas_chile.json
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand

from taller.models.marca import Marca


class Command(BaseCommand):
    help = "Exporta la lista de marcas de Chile a un archivo JSON"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="data/marcas_chile.json",
            help="Ruta al archivo JSON donde guardar las marcas",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"])

        # Crear el directorio si no existe
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Obtener todas las marcas de Chile (o todas si no hay campo country)
        if hasattr(Marca, "country"):
            marcas = Marca.objects.filter(country="CL").order_by("nombre")
        else:
            marcas = Marca.objects.all().order_by("nombre")

        # Extraer solo los nombres
        marcas_list = [m.nombre for m in marcas]

        # Guardar en JSON
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(marcas_list, f, ensure_ascii=False, indent=2)

        self.stdout.write(
            self.style.SUCCESS(f"✅ Exportadas {len(marcas_list)} marcas a {file_path}")
        )
        self.stdout.write(
            self.style.SUCCESS(f"📋 Primeras 10 marcas: {', '.join(marcas_list[:10])}")
        )



