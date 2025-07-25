from django.core.management.base import BaseCommand
from django.db import transaction
from taller.models.marcas_usa import MarcaVehiculo, ModeloVehiculo
from datetime import datetime

class Command(BaseCommand):
    help = 'Importa marcas y modelos de vehículos USA desde 1980'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Eliminar datos existentes antes de importar',
        )

    def handle(self, *args, **options):
        if options['limpiar']:
            self.stdout.write(self.style.WARNING('Eliminando datos existentes...'))
            ModeloVehiculo.objects.all().delete()
            MarcaVehiculo.objects.all().delete()

        with transaction.atomic():
            self.importar_marcas_usa()
            self.importar_modelos_usa()

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Importación completada: {MarcaVehiculo.objects.count()} marcas, '
                f'{ModeloVehiculo.objects.count()} modelos'
            )
        )

    def importar_marcas_usa(self):
        """Importa las principales marcas de vehículos del mercado estadounidense"""
        marcas_data = [
            # Marcas americanas principales
            {'nombre': 'Ford', 'nombre_en': 'Ford', 'pais_origen': 'USA', 'anio_inicio': 1980},
            {'nombre': 'Chevrolet', 'nombre_en': 'Chevrolet', 'pais_origen': 'USA', 'anio_inicio': 1980},
            {'nombre': 'Dodge', 'nombre_en': 'Dodge', 'pais_origen': 'USA', 'anio_inicio': 1980},
            {'nombre': 'Jeep', 'nombre_en': 'Jeep', 'pais_origen': 'USA', 'anio_inicio': 1980},
            {'nombre': 'Cadillac', 'nombre_en': 'Cadillac', 'pais_origen': 'USA', 'anio_inicio': 1980},
            {'nombre': 'Buick', 'nombre_en': 'Buick', 'pais_origen': 'USA', 'anio_inicio': 1980},
            {'nombre': 'GMC', 'nombre_en': 'GMC', 'pais_origen': 'USA', 'anio_inicio': 1980},
            {'nombre': 'Lincoln', 'nombre_en': 'Lincoln', 'pais_origen': 'USA', 'anio_inicio': 1980},
            {'nombre': 'Chrysler', 'nombre_en': 'Chrysler', 'pais_origen': 'USA', 'anio_inicio': 1980},
            
            # Marcas japonesas populares en USA
            {'nombre': 'Toyota', 'nombre_en': 'Toyota', 'pais_origen': 'Japan', 'anio_inicio': 1980},
            {'nombre': 'Honda', 'nombre_en': 'Honda', 'pais_origen': 'Japan', 'anio_inicio': 1980},
            {'nombre': 'Nissan', 'nombre_en': 'Nissan', 'pais_origen': 'Japan', 'anio_inicio': 1980},
            {'nombre': 'Mazda', 'nombre_en': 'Mazda', 'pais_origen': 'Japan', 'anio_inicio': 1980},
            {'nombre': 'Subaru', 'nombre_en': 'Subaru', 'pais_origen': 'Japan', 'anio_inicio': 1980},
            {'nombre': 'Mitsubishi', 'nombre_en': 'Mitsubishi', 'pais_origen': 'Japan', 'anio_inicio': 1980},
            {'nombre': 'Acura', 'nombre_en': 'Acura', 'pais_origen': 'Japan', 'anio_inicio': 1986},
            {'nombre': 'Lexus', 'nombre_en': 'Lexus', 'pais_origen': 'Japan', 'anio_inicio': 1989},
            {'nombre': 'Infiniti', 'nombre_en': 'Infiniti', 'pais_origen': 'Japan', 'anio_inicio': 1989},
            
            # Marcas europeas en USA
            {'nombre': 'BMW', 'nombre_en': 'BMW', 'pais_origen': 'Germany', 'anio_inicio': 1980},
            {'nombre': 'Mercedes-Benz', 'nombre_en': 'Mercedes-Benz', 'pais_origen': 'Germany', 'anio_inicio': 1980},
            {'nombre': 'Audi', 'nombre_en': 'Audi', 'pais_origen': 'Germany', 'anio_inicio': 1980},
            {'nombre': 'Volkswagen', 'nombre_en': 'Volkswagen', 'pais_origen': 'Germany', 'anio_inicio': 1980},
            {'nombre': 'Porsche', 'nombre_en': 'Porsche', 'pais_origen': 'Germany', 'anio_inicio': 1980},
            {'nombre': 'Volvo', 'nombre_en': 'Volvo', 'pais_origen': 'Sweden', 'anio_inicio': 1980},
            
            # Marcas coreanas
            {'nombre': 'Hyundai', 'nombre_en': 'Hyundai', 'pais_origen': 'South Korea', 'anio_inicio': 1986},
            {'nombre': 'Kia', 'nombre_en': 'Kia', 'pais_origen': 'South Korea', 'anio_inicio': 1994},
            {'nombre': 'Genesis', 'nombre_en': 'Genesis', 'pais_origen': 'South Korea', 'anio_inicio': 2015},
            
            # Marcas de lujo y especiales
            {'nombre': 'Tesla', 'nombre_en': 'Tesla', 'pais_origen': 'USA', 'anio_inicio': 2008},
            {'nombre': 'Ram', 'nombre_en': 'Ram', 'pais_origen': 'USA', 'anio_inicio': 2010},
        ]

        for marca_data in marcas_data:
            marca, created = MarcaVehiculo.objects.get_or_create(
                nombre=marca_data['nombre'],
                defaults=marca_data
            )
            if created:
                self.stdout.write(f'✅ Marca creada: {marca.nombre}')

    def importar_modelos_usa(self):
        """Importa modelos populares para cada marca"""
        modelos_data = {
            'Ford': [
                {'nombre': 'F-150', 'nombre_en': 'F-150', 'tipo': 'truck', 'inicio': 1980},
                {'nombre': 'Mustang', 'nombre_en': 'Mustang', 'tipo': 'coupe', 'inicio': 1980},
                {'nombre': 'Explorer', 'nombre_en': 'Explorer', 'tipo': 'suv', 'inicio': 1990},
                {'nombre': 'Focus', 'nombre_en': 'Focus', 'tipo': 'sedan', 'inicio': 2000, 'fin': 2018},
                {'nombre': 'Escape', 'nombre_en': 'Escape', 'tipo': 'suv', 'inicio': 2001},
                {'nombre': 'Fusion', 'nombre_en': 'Fusion', 'tipo': 'sedan', 'inicio': 2006, 'fin': 2020},
                {'nombre': 'Edge', 'nombre_en': 'Edge', 'tipo': 'suv', 'inicio': 2007},
                {'nombre': 'Expedition', 'nombre_en': 'Expedition', 'tipo': 'suv', 'inicio': 1997},
            ],
            'Chevrolet': [
                {'nombre': 'Silverado', 'nombre_en': 'Silverado', 'tipo': 'truck', 'inicio': 1999},
                {'nombre': 'Camaro', 'nombre_en': 'Camaro', 'tipo': 'coupe', 'inicio': 1980, 'fin': 2002},
                {'nombre': 'Camaro', 'nombre_en': 'Camaro', 'tipo': 'coupe', 'inicio': 2010},
                {'nombre': 'Corvette', 'nombre_en': 'Corvette', 'tipo': 'coupe', 'inicio': 1980},
                {'nombre': 'Tahoe', 'nombre_en': 'Tahoe', 'tipo': 'suv', 'inicio': 1995},
                {'nombre': 'Suburban', 'nombre_en': 'Suburban', 'tipo': 'suv', 'inicio': 1980},
                {'nombre': 'Equinox', 'nombre_en': 'Equinox', 'tipo': 'suv', 'inicio': 2005},
                {'nombre': 'Malibu', 'nombre_en': 'Malibu', 'tipo': 'sedan', 'inicio': 1980},
            ],
            'Toyota': [
                {'nombre': 'Camry', 'nombre_en': 'Camry', 'tipo': 'sedan', 'inicio': 1980},
                {'nombre': 'Corolla', 'nombre_en': 'Corolla', 'tipo': 'sedan', 'inicio': 1980},
                {'nombre': 'Prius', 'nombre_en': 'Prius', 'tipo': 'hatchback', 'inicio': 2001},
                {'nombre': 'RAV4', 'nombre_en': 'RAV4', 'tipo': 'suv', 'inicio': 1996},
                {'nombre': 'Highlander', 'nombre_en': 'Highlander', 'tipo': 'suv', 'inicio': 2001},
                {'nombre': 'Tacoma', 'nombre_en': 'Tacoma', 'tipo': 'truck', 'inicio': 1995},
                {'nombre': 'Tundra', 'nombre_en': 'Tundra', 'tipo': 'truck', 'inicio': 2000},
                {'nombre': 'Sienna', 'nombre_en': 'Sienna', 'tipo': 'van', 'inicio': 1998},
            ],
            'Honda': [
                {'nombre': 'Civic', 'nombre_en': 'Civic', 'tipo': 'sedan', 'inicio': 1980},
                {'nombre': 'Accord', 'nombre_en': 'Accord', 'tipo': 'sedan', 'inicio': 1980},
                {'nombre': 'CR-V', 'nombre_en': 'CR-V', 'tipo': 'suv', 'inicio': 1997},
                {'nombre': 'Pilot', 'nombre_en': 'Pilot', 'tipo': 'suv', 'inicio': 2003},
                {'nombre': 'Odyssey', 'nombre_en': 'Odyssey', 'tipo': 'van', 'inicio': 1995},
                {'nombre': 'Ridgeline', 'nombre_en': 'Ridgeline', 'tipo': 'truck', 'inicio': 2006},
                {'nombre': 'Fit', 'nombre_en': 'Fit', 'tipo': 'hatchback', 'inicio': 2007, 'fin': 2020},
            ],
            'Nissan': [
                {'nombre': 'Altima', 'nombre_en': 'Altima', 'tipo': 'sedan', 'inicio': 1993},
                {'nombre': 'Sentra', 'nombre_en': 'Sentra', 'tipo': 'sedan', 'inicio': 1980},
                {'nombre': 'Rogue', 'nombre_en': 'Rogue', 'tipo': 'suv', 'inicio': 2008},
                {'nombre': 'Pathfinder', 'nombre_en': 'Pathfinder', 'tipo': 'suv', 'inicio': 1987},
                {'nombre': 'Armada', 'nombre_en': 'Armada', 'tipo': 'suv', 'inicio': 2004},
                {'nombre': 'Titan', 'nombre_en': 'Titan', 'tipo': 'truck', 'inicio': 2004},
                {'nombre': 'Maxima', 'nombre_en': 'Maxima', 'tipo': 'sedan', 'inicio': 1980},
            ],
            'BMW': [
                {'nombre': 'Serie 3', 'nombre_en': '3 Series', 'tipo': 'sedan', 'inicio': 1980},
                {'nombre': 'Serie 5', 'nombre_en': '5 Series', 'tipo': 'sedan', 'inicio': 1980},
                {'nombre': 'Serie 7', 'nombre_en': '7 Series', 'tipo': 'sedan', 'inicio': 1980},
                {'nombre': 'X3', 'nombre_en': 'X3', 'tipo': 'suv', 'inicio': 2004},
                {'nombre': 'X5', 'nombre_en': 'X5', 'tipo': 'suv', 'inicio': 2000},
                {'nombre': 'X1', 'nombre_en': 'X1', 'tipo': 'suv', 'inicio': 2012},
            ],
            'Mercedes-Benz': [
                {'nombre': 'Clase C', 'nombre_en': 'C-Class', 'tipo': 'sedan', 'inicio': 1994},
                {'nombre': 'Clase E', 'nombre_en': 'E-Class', 'tipo': 'sedan', 'inicio': 1980},
                {'nombre': 'Clase S', 'nombre_en': 'S-Class', 'tipo': 'sedan', 'inicio': 1980},
                {'nombre': 'GLE', 'nombre_en': 'GLE', 'tipo': 'suv', 'inicio': 1998},
                {'nombre': 'GLC', 'nombre_en': 'GLC', 'tipo': 'suv', 'inicio': 2016},
            ],
            'Tesla': [
                {'nombre': 'Model S', 'nombre_en': 'Model S', 'tipo': 'sedan', 'inicio': 2012},
                {'nombre': 'Model 3', 'nombre_en': 'Model 3', 'tipo': 'sedan', 'inicio': 2017},
                {'nombre': 'Model X', 'nombre_en': 'Model X', 'tipo': 'suv', 'inicio': 2015},
                {'nombre': 'Model Y', 'nombre_en': 'Model Y', 'tipo': 'suv', 'inicio': 2020},
            ],
        }

        for marca_nombre, modelos in modelos_data.items():
            try:
                marca = MarcaVehiculo.objects.get(nombre=marca_nombre)
                for modelo_data in modelos:
                    modelo, created = ModeloVehiculo.objects.get_or_create(
                        marca=marca,
                        nombre=modelo_data['nombre'],
                        defaults={
                            'nombre_en': modelo_data['nombre_en'],
                            'tipo_vehiculo': modelo_data['tipo'],
                            'anio_inicio': modelo_data['inicio'],
                            'anio_fin': modelo_data.get('fin'),
                        }
                    )
                    if created:
                        self.stdout.write(f'✅ Modelo creado: {marca.nombre} {modelo.nombre}')
            except MarcaVehiculo.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Marca no encontrada: {marca_nombre}')
                )
