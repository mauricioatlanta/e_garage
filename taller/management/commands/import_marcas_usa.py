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
            'Audi': [
                {'nombre': 'A3', 'nombre_en': 'A3', 'tipo': 'sedan', 'inicio': 2006},
                {'nombre': 'A4', 'nombre_en': 'A4', 'tipo': 'sedan', 'inicio': 1996},
                {'nombre': 'A6', 'nombre_en': 'A6', 'tipo': 'sedan', 'inicio': 1998},
                {'nombre': 'A8', 'nombre_en': 'A8', 'tipo': 'sedan', 'inicio': 1997},
                {'nombre': 'Q3', 'nombre_en': 'Q3', 'tipo': 'suv', 'inicio': 2015},
                {'nombre': 'Q5', 'nombre_en': 'Q5', 'tipo': 'suv', 'inicio': 2009},
                {'nombre': 'Q7', 'nombre_en': 'Q7', 'tipo': 'suv', 'inicio': 2007},
                {'nombre': 'TT', 'nombre_en': 'TT', 'tipo': 'coupe', 'inicio': 2000},
            ],
            'Volkswagen': [
                {'nombre': 'Jetta', 'nombre_en': 'Jetta', 'tipo': 'sedan', 'inicio': 1980},
                {'nombre': 'Passat', 'nombre_en': 'Passat', 'tipo': 'sedan', 'inicio': 1990, 'fin': 2022},
                {'nombre': 'Golf', 'nombre_en': 'Golf', 'tipo': 'hatchback', 'inicio': 1980},
                {'nombre': 'Beetle', 'nombre_en': 'Beetle', 'tipo': 'hatchback', 'inicio': 1998, 'fin': 2019},
                {'nombre': 'Tiguan', 'nombre_en': 'Tiguan', 'tipo': 'suv', 'inicio': 2009},
                {'nombre': 'Atlas', 'nombre_en': 'Atlas', 'tipo': 'suv', 'inicio': 2018},
                {'nombre': 'Touareg', 'nombre_en': 'Touareg', 'tipo': 'suv', 'inicio': 2004, 'fin': 2017},
            ],
            'Porsche': [
                {'nombre': '911', 'nombre_en': '911', 'tipo': 'coupe', 'inicio': 1980},
                {'nombre': 'Boxster', 'nombre_en': 'Boxster', 'tipo': 'convertible', 'inicio': 1997},
                {'nombre': 'Cayman', 'nombre_en': 'Cayman', 'tipo': 'coupe', 'inicio': 2006},
                {'nombre': 'Cayenne', 'nombre_en': 'Cayenne', 'tipo': 'suv', 'inicio': 2003},
                {'nombre': 'Macan', 'nombre_en': 'Macan', 'tipo': 'suv', 'inicio': 2014},
                {'nombre': 'Panamera', 'nombre_en': 'Panamera', 'tipo': 'sedan', 'inicio': 2010},
            ],
            'Acura': [
                {'nombre': 'TL', 'nombre_en': 'TL', 'tipo': 'sedan', 'inicio': 1999, 'fin': 2014},
                {'nombre': 'TLX', 'nombre_en': 'TLX', 'tipo': 'sedan', 'inicio': 2015},
                {'nombre': 'TSX', 'nombre_en': 'TSX', 'tipo': 'sedan', 'inicio': 2004, 'fin': 2014},
                {'nombre': 'ILX', 'nombre_en': 'ILX', 'tipo': 'sedan', 'inicio': 2013},
                {'nombre': 'MDX', 'nombre_en': 'MDX', 'tipo': 'suv', 'inicio': 2001},
                {'nombre': 'RDX', 'nombre_en': 'RDX', 'tipo': 'suv', 'inicio': 2007},
                {'nombre': 'NSX', 'nombre_en': 'NSX', 'tipo': 'coupe', 'inicio': 1991, 'fin': 2005},
            ],
            'Lexus': [
                {'nombre': 'ES', 'nombre_en': 'ES', 'tipo': 'sedan', 'inicio': 1989},
                {'nombre': 'IS', 'nombre_en': 'IS', 'tipo': 'sedan', 'inicio': 2001},
                {'nombre': 'GS', 'nombre_en': 'GS', 'tipo': 'sedan', 'inicio': 1993, 'fin': 2020},
                {'nombre': 'LS', 'nombre_en': 'LS', 'tipo': 'sedan', 'inicio': 1990},
                {'nombre': 'RX', 'nombre_en': 'RX', 'tipo': 'suv', 'inicio': 1999},
                {'nombre': 'GX', 'nombre_en': 'GX', 'tipo': 'suv', 'inicio': 2003},
                {'nombre': 'LX', 'nombre_en': 'LX', 'tipo': 'suv', 'inicio': 1996},
                {'nombre': 'NX', 'nombre_en': 'NX', 'tipo': 'suv', 'inicio': 2015},
            ],
            'Infiniti': [
                {'nombre': 'Q50', 'nombre_en': 'Q50', 'tipo': 'sedan', 'inicio': 2014},
                {'nombre': 'Q60', 'nombre_en': 'Q60', 'tipo': 'coupe', 'inicio': 2017},
                {'nombre': 'Q70', 'nombre_en': 'Q70', 'tipo': 'sedan', 'inicio': 2014, 'fin': 2019},
                {'nombre': 'QX50', 'nombre_en': 'QX50', 'tipo': 'suv', 'inicio': 2008},
                {'nombre': 'QX60', 'nombre_en': 'QX60', 'tipo': 'suv', 'inicio': 2013},
                {'nombre': 'QX80', 'nombre_en': 'QX80', 'tipo': 'suv', 'inicio': 2014},
                {'nombre': 'G35', 'nombre_en': 'G35', 'tipo': 'sedan', 'inicio': 2003, 'fin': 2008},
            ],
            'Mazda': [
                {'nombre': 'Mazda3', 'nombre_en': 'Mazda3', 'tipo': 'sedan', 'inicio': 2004},
                {'nombre': 'Mazda6', 'nombre_en': 'Mazda6', 'tipo': 'sedan', 'inicio': 2003},
                {'nombre': 'CX-3', 'nombre_en': 'CX-3', 'tipo': 'suv', 'inicio': 2016},
                {'nombre': 'CX-5', 'nombre_en': 'CX-5', 'tipo': 'suv', 'inicio': 2013},
                {'nombre': 'CX-9', 'nombre_en': 'CX-9', 'tipo': 'suv', 'inicio': 2007},
                {'nombre': 'MX-5 Miata', 'nombre_en': 'MX-5 Miata', 'tipo': 'convertible', 'inicio': 1990},
                {'nombre': 'RX-8', 'nombre_en': 'RX-8', 'tipo': 'coupe', 'inicio': 2004, 'fin': 2012},
            ],
            'Subaru': [
                {'nombre': 'Impreza', 'nombre_en': 'Impreza', 'tipo': 'sedan', 'inicio': 1993},
                {'nombre': 'Legacy', 'nombre_en': 'Legacy', 'tipo': 'sedan', 'inicio': 1990},
                {'nombre': 'Outback', 'nombre_en': 'Outback', 'tipo': 'wagon', 'inicio': 1995},
                {'nombre': 'Forester', 'nombre_en': 'Forester', 'tipo': 'suv', 'inicio': 1998},
                {'nombre': 'Ascent', 'nombre_en': 'Ascent', 'tipo': 'suv', 'inicio': 2019},
                {'nombre': 'Crosstrek', 'nombre_en': 'Crosstrek', 'tipo': 'suv', 'inicio': 2013},
                {'nombre': 'WRX', 'nombre_en': 'WRX', 'tipo': 'sedan', 'inicio': 2002},
                {'nombre': 'BRZ', 'nombre_en': 'BRZ', 'tipo': 'coupe', 'inicio': 2013},
            ],
            'Mitsubishi': [
                {'nombre': 'Lancer', 'nombre_en': 'Lancer', 'tipo': 'sedan', 'inicio': 1980, 'fin': 2017},
                {'nombre': 'Outlander', 'nombre_en': 'Outlander', 'tipo': 'suv', 'inicio': 2003},
                {'nombre': 'Eclipse Cross', 'nombre_en': 'Eclipse Cross', 'tipo': 'suv', 'inicio': 2018},
                {'nombre': 'Mirage', 'nombre_en': 'Mirage', 'tipo': 'hatchback', 'inicio': 2014},
                {'nombre': 'Outlander Sport', 'nombre_en': 'Outlander Sport', 'tipo': 'suv', 'inicio': 2011},
                {'nombre': 'Eclipse', 'nombre_en': 'Eclipse', 'tipo': 'coupe', 'inicio': 1990, 'fin': 2012},
            ],
            'Hyundai': [
                {'nombre': 'Elantra', 'nombre_en': 'Elantra', 'tipo': 'sedan', 'inicio': 1990},
                {'nombre': 'Sonata', 'nombre_en': 'Sonata', 'tipo': 'sedan', 'inicio': 1989},
                {'nombre': 'Accent', 'nombre_en': 'Accent', 'tipo': 'sedan', 'inicio': 1995},
                {'nombre': 'Tucson', 'nombre_en': 'Tucson', 'tipo': 'suv', 'inicio': 2005},
                {'nombre': 'Santa Fe', 'nombre_en': 'Santa Fe', 'tipo': 'suv', 'inicio': 2001},
                {'nombre': 'Palisade', 'nombre_en': 'Palisade', 'tipo': 'suv', 'inicio': 2020},
                {'nombre': 'Veloster', 'nombre_en': 'Veloster', 'tipo': 'hatchback', 'inicio': 2012},
                {'nombre': 'Genesis', 'nombre_en': 'Genesis', 'tipo': 'sedan', 'inicio': 2009, 'fin': 2016},
            ],
            'Kia': [
                {'nombre': 'Forte', 'nombre_en': 'Forte', 'tipo': 'sedan', 'inicio': 2010},
                {'nombre': 'Optima', 'nombre_en': 'Optima', 'tipo': 'sedan', 'inicio': 2001, 'fin': 2020},
                {'nombre': 'K5', 'nombre_en': 'K5', 'tipo': 'sedan', 'inicio': 2021},
                {'nombre': 'Soul', 'nombre_en': 'Soul', 'tipo': 'hatchback', 'inicio': 2010},
                {'nombre': 'Sportage', 'nombre_en': 'Sportage', 'tipo': 'suv', 'inicio': 1995},
                {'nombre': 'Sorento', 'nombre_en': 'Sorento', 'tipo': 'suv', 'inicio': 2003},
                {'nombre': 'Telluride', 'nombre_en': 'Telluride', 'tipo': 'suv', 'inicio': 2020},
                {'nombre': 'Rio', 'nombre_en': 'Rio', 'tipo': 'sedan', 'inicio': 2001},
            ],
            'Genesis': [
                {'nombre': 'G70', 'nombre_en': 'G70', 'tipo': 'sedan', 'inicio': 2019},
                {'nombre': 'G80', 'nombre_en': 'G80', 'tipo': 'sedan', 'inicio': 2017},
                {'nombre': 'G90', 'nombre_en': 'G90', 'tipo': 'sedan', 'inicio': 2017},
                {'nombre': 'GV70', 'nombre_en': 'GV70', 'tipo': 'suv', 'inicio': 2022},
                {'nombre': 'GV80', 'nombre_en': 'GV80', 'tipo': 'suv', 'inicio': 2021},
            ],
            'Volvo': [
                {'nombre': 'S60', 'nombre_en': 'S60', 'tipo': 'sedan', 'inicio': 2001},
                {'nombre': 'S90', 'nombre_en': 'S90', 'tipo': 'sedan', 'inicio': 1997, 'fin': 1998},
                {'nombre': 'S90', 'nombre_en': 'S90', 'tipo': 'sedan', 'inicio': 2017},
                {'nombre': 'XC40', 'nombre_en': 'XC40', 'tipo': 'suv', 'inicio': 2018},
                {'nombre': 'XC60', 'nombre_en': 'XC60', 'tipo': 'suv', 'inicio': 2009},
                {'nombre': 'XC90', 'nombre_en': 'XC90', 'tipo': 'suv', 'inicio': 2003},
                {'nombre': 'V60', 'nombre_en': 'V60', 'tipo': 'wagon', 'inicio': 2011},
            ],
            'Dodge': [
                {'nombre': 'Charger', 'nombre_en': 'Charger', 'tipo': 'sedan', 'inicio': 2006},
                {'nombre': 'Challenger', 'nombre_en': 'Challenger', 'tipo': 'coupe', 'inicio': 2008},
                {'nombre': 'Durango', 'nombre_en': 'Durango', 'tipo': 'suv', 'inicio': 1998},
                {'nombre': 'Journey', 'nombre_en': 'Journey', 'tipo': 'suv', 'inicio': 2009, 'fin': 2020},
                {'nombre': 'Grand Caravan', 'nombre_en': 'Grand Caravan', 'tipo': 'van', 'inicio': 1984, 'fin': 2020},
                {'nombre': 'Avenger', 'nombre_en': 'Avenger', 'tipo': 'sedan', 'inicio': 1995, 'fin': 1999},
                {'nombre': 'Dart', 'nombre_en': 'Dart', 'tipo': 'sedan', 'inicio': 2013, 'fin': 2016},
            ],
            'Jeep': [
                {'nombre': 'Wrangler', 'nombre_en': 'Wrangler', 'tipo': 'suv', 'inicio': 1987},
                {'nombre': 'Grand Cherokee', 'nombre_en': 'Grand Cherokee', 'tipo': 'suv', 'inicio': 1993},
                {'nombre': 'Cherokee', 'nombre_en': 'Cherokee', 'tipo': 'suv', 'inicio': 2014},
                {'nombre': 'Compass', 'nombre_en': 'Compass', 'tipo': 'suv', 'inicio': 2007},
                {'nombre': 'Patriot', 'nombre_en': 'Patriot', 'tipo': 'suv', 'inicio': 2007, 'fin': 2017},
                {'nombre': 'Renegade', 'nombre_en': 'Renegade', 'tipo': 'suv', 'inicio': 2015},
                {'nombre': 'Gladiator', 'nombre_en': 'Gladiator', 'tipo': 'truck', 'inicio': 2020},
            ],
            'Cadillac': [
                {'nombre': 'Escalade', 'nombre_en': 'Escalade', 'tipo': 'suv', 'inicio': 1999},
                {'nombre': 'CTS', 'nombre_en': 'CTS', 'tipo': 'sedan', 'inicio': 2003, 'fin': 2019},
                {'nombre': 'CT6', 'nombre_en': 'CT6', 'tipo': 'sedan', 'inicio': 2016, 'fin': 2020},
                {'nombre': 'XT5', 'nombre_en': 'XT5', 'tipo': 'suv', 'inicio': 2017},
                {'nombre': 'XT6', 'nombre_en': 'XT6', 'tipo': 'suv', 'inicio': 2020},
                {'nombre': 'ATS', 'nombre_en': 'ATS', 'tipo': 'sedan', 'inicio': 2013, 'fin': 2019},
                {'nombre': 'SRX', 'nombre_en': 'SRX', 'tipo': 'suv', 'inicio': 2004, 'fin': 2016},
            ],
            'Buick': [
                {'nombre': 'Enclave', 'nombre_en': 'Enclave', 'tipo': 'suv', 'inicio': 2008},
                {'nombre': 'Encore', 'nombre_en': 'Encore', 'tipo': 'suv', 'inicio': 2013},
                {'nombre': 'Envision', 'nombre_en': 'Envision', 'tipo': 'suv', 'inicio': 2016},
                {'nombre': 'LaCrosse', 'nombre_en': 'LaCrosse', 'tipo': 'sedan', 'inicio': 2005, 'fin': 2019},
                {'nombre': 'Regal', 'nombre_en': 'Regal', 'tipo': 'sedan', 'inicio': 1988, 'fin': 2020},
                {'nombre': 'Verano', 'nombre_en': 'Verano', 'tipo': 'sedan', 'inicio': 2012, 'fin': 2017},
            ],
            'GMC': [
                {'nombre': 'Sierra', 'nombre_en': 'Sierra', 'tipo': 'truck', 'inicio': 1999},
                {'nombre': 'Yukon', 'nombre_en': 'Yukon', 'tipo': 'suv', 'inicio': 1992},
                {'nombre': 'Acadia', 'nombre_en': 'Acadia', 'tipo': 'suv', 'inicio': 2007},
                {'nombre': 'Terrain', 'nombre_en': 'Terrain', 'tipo': 'suv', 'inicio': 2010},
                {'nombre': 'Canyon', 'nombre_en': 'Canyon', 'tipo': 'truck', 'inicio': 2004, 'fin': 2012},
                {'nombre': 'Canyon', 'nombre_en': 'Canyon', 'tipo': 'truck', 'inicio': 2015},
                {'nombre': 'Savana', 'nombre_en': 'Savana', 'tipo': 'van', 'inicio': 1996},
            ],
            'Lincoln': [
                {'nombre': 'Navigator', 'nombre_en': 'Navigator', 'tipo': 'suv', 'inicio': 1998},
                {'nombre': 'Aviator', 'nombre_en': 'Aviator', 'tipo': 'suv', 'inicio': 2003, 'fin': 2005},
                {'nombre': 'Aviator', 'nombre_en': 'Aviator', 'tipo': 'suv', 'inicio': 2020},
                {'nombre': 'Corsair', 'nombre_en': 'Corsair', 'tipo': 'suv', 'inicio': 2020},
                {'nombre': 'Nautilus', 'nombre_en': 'Nautilus', 'tipo': 'suv', 'inicio': 2019},
                {'nombre': 'Continental', 'nombre_en': 'Continental', 'tipo': 'sedan', 'inicio': 2017, 'fin': 2020},
                {'nombre': 'MKZ', 'nombre_en': 'MKZ', 'tipo': 'sedan', 'inicio': 2007, 'fin': 2020},
            ],
            'Chrysler': [
                {'nombre': '300', 'nombre_en': '300', 'tipo': 'sedan', 'inicio': 2005},
                {'nombre': 'Pacifica', 'nombre_en': 'Pacifica', 'tipo': 'van', 'inicio': 2017},
                {'nombre': 'Town & Country', 'nombre_en': 'Town & Country', 'tipo': 'van', 'inicio': 1990, 'fin': 2016},
                {'nombre': 'Sebring', 'nombre_en': 'Sebring', 'tipo': 'sedan', 'inicio': 1995, 'fin': 2010},
                {'nombre': 'PT Cruiser', 'nombre_en': 'PT Cruiser', 'tipo': 'wagon', 'inicio': 2001, 'fin': 2010},
                {'nombre': '200', 'nombre_en': '200', 'tipo': 'sedan', 'inicio': 2011, 'fin': 2017},
            ],
            'Ram': [
                {'nombre': '1500', 'nombre_en': '1500', 'tipo': 'truck', 'inicio': 2011},
                {'nombre': '2500', 'nombre_en': '2500', 'tipo': 'truck', 'inicio': 2011},
                {'nombre': '3500', 'nombre_en': '3500', 'tipo': 'truck', 'inicio': 2011},
                {'nombre': 'ProMaster', 'nombre_en': 'ProMaster', 'tipo': 'van', 'inicio': 2014},
                {'nombre': 'ProMaster City', 'nombre_en': 'ProMaster City', 'tipo': 'van', 'inicio': 2015},
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
