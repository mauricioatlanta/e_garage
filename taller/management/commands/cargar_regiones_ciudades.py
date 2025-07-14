import json
from django.core.management.base import BaseCommand
	from taller.models.region_ciudad import TallerRegion, TallerCiudad
from pathlib import Path

class Command(BaseCommand):
    help = 'Carga regiones y ciudades de Chile desde un JSON externo'

    def handle(self, *args, **kwargs):
        json_path = Path('data/regiones_y_ciudades_chile.json')
        if not json_path.exists():
            self.stdout.write(self.style.ERROR('❌ No se encontró el archivo regiones_y_ciudades_chile.json'))
            return

        with open(json_path, encoding='utf-8') as f:
            datos = json.load(f)

        nuevas_regiones = 0
        nuevas_ciudades = 0

        for nombre_region, ciudades in datos.items():
            region, region_creada = Region.objects.get_or_create(nombre=nombre_region)
            if region_creada:
                nuevas_regiones += 1

            for ciudad in ciudades:
                _, ciudad_creada = TallerCiudad.objects.get_or_create(nombre=ciudad, region=region)
                if ciudad_creada:
                    nuevas_ciudades += 1

        self.stdout.write(self.style.SUCCESS(f'✅ {nuevas_regiones} regiones y {nuevas_ciudades} ciudades cargadas exitosamente.'))