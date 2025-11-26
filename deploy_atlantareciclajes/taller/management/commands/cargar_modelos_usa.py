"""
Comando de gestión para cargar modelos de vehículos para USA
Ejecutar: python manage.py cargar_modelos_usa
"""

from django.core.management.base import BaseCommand
from django.db import models

from taller.models.marca import Marca
from taller.models.modelo import Modelo


class Command(BaseCommand):
    help = "Carga modelos comunes de vehículos para USA por marca"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚗 Cargando modelos de vehículos para USA\n"))

        # Modelos populares por marca en USA
        marcas_modelos = {
            "Ford": [
                "F-150",
                "F-250",
                "F-350",
                "Mustang",
                "Explorer",
                "Escape",
                "Edge",
                "Expedition",
                "Ranger",
                "Bronco",
                "Focus",
                "Fusion",
                "Taurus",
            ],
            "Chevrolet": [
                "Silverado",
                "Tahoe",
                "Suburban",
                "Equinox",
                "Traverse",
                "Malibu",
                "Camaro",
                "Corvette",
                "Cruze",
                "Impala",
                "Blazer",
                "Trailblazer",
            ],
            "Toyota": [
                "Camry",
                "Corolla",
                "RAV4",
                "Highlander",
                "Tacoma",
                "Tundra",
                "4Runner",
                "Prius",
                "Sienna",
                "Sequoia",
                "Land Cruiser",
                "Avalon",
            ],
            "Honda": [
                "Civic",
                "Accord",
                "CR-V",
                "Pilot",
                "Odyssey",
                "Ridgeline",
                "Passport",
                "HR-V",
                "Insight",
                "Fit",
            ],
            "Nissan": [
                "Altima",
                "Sentra",
                "Rogue",
                "Pathfinder",
                "Armada",
                "Frontier",
                "Titan",
                "Murano",
                "Maxima",
                "Versa",
            ],
            "Dodge": [
                "Ram 1500",
                "Ram 2500",
                "Ram 3500",
                "Charger",
                "Challenger",
                "Durango",
                "Journey",
                "Grand Caravan",
            ],
            "Jeep": [
                "Wrangler",
                "Grand Cherokee",
                "Cherokee",
                "Compass",
                "Renegade",
                "Gladiator",
                "Wagoneer",
                "Grand Wagoneer",
            ],
            "GMC": [
                "Sierra 1500",
                "Sierra 2500",
                "Sierra 3500",
                "Yukon",
                "Yukon XL",
                "Acadia",
                "Terrain",
                "Canyon",
            ],
            "Ram": ["1500", "2500", "3500", "4500", "5500", "ProMaster", "ProMaster City"],
            "Subaru": [
                "Outback",
                "Forester",
                "Crosstrek",
                "Ascent",
                "Legacy",
                "Impreza",
                "WRX",
                "BRZ",
            ],
            "Mazda": ["CX-5", "CX-9", "CX-30", "Mazda3", "Mazda6", "MX-5 Miata", "CX-50"],
            "Hyundai": [
                "Elantra",
                "Sonata",
                "Tucson",
                "Santa Fe",
                "Palisade",
                "Kona",
                "Venue",
                "Ioniq",
            ],
            "Kia": [
                "Forte",
                "Optima",
                "Sorento",
                "Sportage",
                "Telluride",
                "Soul",
                "Rio",
                "Stinger",
            ],
            "Volkswagen": ["Jetta", "Passat", "Atlas", "Tiguan", "Golf", "Arteon", "ID.4"],
            "BMW": ["3 Series", "5 Series", "X3", "X5", "X1", "X7", "7 Series", "M3", "M5"],
            "Mercedes-Benz": [
                "C-Class",
                "E-Class",
                "S-Class",
                "GLC",
                "GLE",
                "GLS",
                "A-Class",
                "CLA",
            ],
            "Audi": ["A4", "A6", "Q5", "Q7", "A3", "Q3", "e-tron", "A5"],
            "Lexus": ["RX", "NX", "ES", "GX", "LX", "IS", "LS", "UX"],
            "Acura": ["MDX", "RDX", "TLX", "ILX", "NSX", "Integra"],
            "Infiniti": ["Q50", "Q60", "QX50", "QX60", "QX80", "QX55"],
            "Cadillac": ["Escalade", "XT5", "XT6", "CT5", "CT4", "Lyriq"],
            "Lincoln": ["Navigator", "Aviator", "Corsair", "Nautilus", "Continental"],
            "Buick": ["Encore", "Envision", "Enclave", "Regal"],
            "Chrysler": ["Pacifica", "300", "Voyager"],
            "Tesla": ["Model 3", "Model Y", "Model S", "Model X", "Cybertruck"],
            "Volvo": ["XC60", "XC90", "S60", "S90", "XC40", "V60"],
            "Genesis": ["G70", "G80", "G90", "GV70", "GV80"],
            "Porsche": ["911", "Cayenne", "Macan", "Panamera", "Taycan"],
            "Jaguar": ["F-Pace", "E-Pace", "XF", "XE", "F-Type"],
            "Land Rover": ["Range Rover", "Range Rover Sport", "Discovery", "Defender", "Evoque"],
            "Alfa Romeo": ["Giulia", "Stelvio", "Tonale"],
            "Mitsubishi": ["Outlander", "Eclipse Cross", "Outlander Sport", "Mirage"],
            "Mini": ["Cooper", "Countryman", "Clubman"],
            "Fiat": ["500", "500X", "500L"],
            "Maserati": ["Ghibli", "Levante", "Quattroporte"],
            "Bentley": ["Continental", "Bentayga", "Flying Spur"],
            "Rolls-Royce": ["Ghost", "Phantom", "Cullinan", "Wraith"],
            "Aston Martin": ["DB11", "Vantage", "DBX"],
            "McLaren": ["720S", "570S", "Artura"],
            "Ferrari": ["488", "F8", "Roma", "SF90"],
            "Lamborghini": ["Huracán", "Aventador", "Urus"],
        }

        total_creados = 0
        total_existentes = 0
        marcas_sin_encontrar = []

        for marca_nombre, modelos_lista in marcas_modelos.items():
            # Buscar la marca
            try:
                marca = Marca.objects.get(nombre=marca_nombre, country="US")
                self.stdout.write(f"\n📦 {marca_nombre}:")
            except Marca.DoesNotExist:
                marcas_sin_encontrar.append(marca_nombre)
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Marca '{marca_nombre}' no encontrada (country='US')")
                )
                continue

            # Crear modelos para esta marca
            for modelo_nombre in modelos_lista:
                modelo, created = Modelo.objects.get_or_create(
                    nombre=modelo_nombre,
                    marca=marca,
                    country="US",
                    defaults={"nombre": modelo_nombre, "marca": marca, "country": "US"},
                )

                if created:
                    self.stdout.write(f"  ✅ Creado: {modelo_nombre}")
                    total_creados += 1
                else:
                    self.stdout.write(f"  📍 Ya existe: {modelo_nombre}")
                    total_existentes += 1

        # Resumen
        self.stdout.write(self.style.SUCCESS("\n🎉 RESUMEN:"))
        self.stdout.write(self.style.SUCCESS(f"✅ Modelos creados: {total_creados}"))
        self.stdout.write(f"📍 Modelos ya existentes: {total_existentes}")
        self.stdout.write(
            self.style.SUCCESS(
                f"🚗 Total modelos USA: {Modelo.objects.filter(country='US').count()}"
            )
        )

        if marcas_sin_encontrar:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️  Marcas no encontradas ({len(marcas_sin_encontrar)}): {', '.join(marcas_sin_encontrar)}"
                )
            )
            self.stdout.write("   💡 Ejecuta primero: python manage.py cargar_marcas_usa")

        # Estadísticas por marca
        self.stdout.write("\n📊 Estadísticas por marca:")
        marcas_con_modelos = (
            Modelo.objects.filter(country="US")
            .values("marca__nombre")
            .annotate(total=models.Count("id"))
            .order_by("-total")[:10]
        )
        for item in marcas_con_modelos:
            self.stdout.write(f"  {item['marca__nombre']}: {item['total']} modelos")
