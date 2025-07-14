import json
from django.core.management.base import BaseCommand
	from taller.models.region_ciudad import TallerRegion, TallerCiudad

class Command(BaseCommand):
    help = "Carga regiones y ciudades desde el archivo regiones_ciudades.json"

    def handle(self, *args, **kwargs):
        self.stdout.write("🧹 Eliminando regiones y ciudades existentes...")
        TallerCiudad.objects.all().delete()
        TallerRegion.objects.all().delete()

        try:
            with open('regiones_ciudades.json', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR("❌ Archivo regiones_ciudades.json no encontrado."))
            return

        self.stdout.write("📥 Cargando regiones y ciudades desde archivo...")
        for item in data:
            region_name = item["region"]
            region = TallerRegion.objects.create(nombre=region_name)
            for ciudad_name in item["ciudades"]:
                TallerCiudad.objects.create(nombre=ciudad_name, region=region)

        self.stdout.write(self.style.SUCCESS("✅ Regiones y ciudades cargadas correctamente."))