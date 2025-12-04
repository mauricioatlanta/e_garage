"""
Comando de gestión para cargar marcas de vehículos para Chile desde JSON
Ejecutar: python manage.py load_marcas_chile --file data/marcas_chile.json
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from taller.models.marca import Marca


class Command(BaseCommand):
    help = "Carga o actualiza la lista de marcas para Chile"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="data/marcas_chile.json",
            help="Ruta al archivo JSON con la lista de marcas",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = Path(options["file"])

        if not file_path.exists():
            self.stderr.write(self.style.ERROR(f"Archivo no encontrado: {file_path}"))
            return

        with file_path.open("r", encoding="utf-8") as f:
            marcas = json.load(f)

        creadas = 0
        existentes = 0

        for nombre in marcas:
            nombre_limpio = nombre.strip()

            if not nombre_limpio:
                continue

            # Usar get_or_create con country para evitar duplicados
            obj, created = Marca.objects.get_or_create(
                nombre=nombre_limpio, country="CL", defaults={}
            )

            if created:
                creadas += 1
            else:
                existentes += 1

        self.stdout.write(
            self.style.SUCCESS(f"Proceso terminado. Creadas: {creadas}, ya existían: {existentes}")
        )
