from django.core.management.base import BaseCommand

from taller.models.marca import Marca
from taller.models.modelo import Modelo


class Command(BaseCommand):
    help = "Cargar marcas y modelos específicos para Chile"

    def handle(self, *args, **options):
        # Datos específicos para Chile
        marcas_modelos_chile = {
            "Audi": ["A3", "A4", "A6", "Q2", "Q3", "Q5", "Q7", "Q8", "TT", "e-tron"],
            "BYD": [
                "Dolphin",
                "Seal",
                "Yuan Plus (Atto 3)",
                "Tang",
                "Song",
                "Han",
                "Qin",
                "e6",
                "Dolphin Mini",
                "Yuan",
            ],
            "Changan": [
                "Alsvin",
                "CS15",
                "CS35",
                "CS55",
                "CS75",
                "UNI-T",
                "UNI-K",
                "Hunter",
                "Kaicene F70",
                "Star Truck",
            ],
            "Chery": [
                "Tiggo 2",
                "Tiggo 3",
                "Tiggo 4",
                "Tiggo 7",
                "Tiggo 8",
                "Arrizo 3",
                "Arrizo 5",
                "Arrizo 7",
                "QQ",
                "Fulwin",
            ],
            "Chevrolet": [
                "Sail",
                "Aveo",
                "Spark",
                "Onix",
                "Cruze",
                "Tracker",
                "Captiva",
                "Trailblazer",
                "Colorado",
                "Silverado",
            ],
            "Citroën": [
                "C3",
                "C4",
                "C5",
                "C-Elysée",
                "Berlingo",
                "Jumper",
                "Jumpy",
                "DS3",
                "DS4",
                "Picasso",
            ],
            "Daihatsu": [
                "Charade",
                "Cuore",
                "Terios",
                "Rocky",
                "Sirion",
                "Feroza",
                "Applause",
                "Hijet",
                "Move",
                "Mira",
            ],
            "Fiat": [
                "Uno",
                "Palio",
                "Siena",
                "Punto",
                "500",
                "Panda",
                "Cronos",
                "Strada",
                "Toro",
                "Fiorino",
            ],
            "Ford": [
                "Escort",
                "Focus",
                "Fiesta",
                "Ka",
                "Mustang",
                "Ecosport",
                "Explorer",
                "Edge",
                "Ranger",
                "F-150",
            ],
            "Great Wall": [
                "Wingle 5",
                "Wingle 7",
                "Poer",
                "C30",
                "C50",
                "Haval H1",
                "Haval H2",
                "Haval H6",
                "Hover",
                "Steed",
            ],
            "Honda": [
                "Civic",
                "Accord",
                "Fit",
                "City",
                "CR-V",
                "HR-V",
                "Pilot",
                "Odyssey",
                "Ridgeline",
                "WR-V",
            ],
            "Hyundai": [
                "Accent",
                "Elantra",
                "Sonata",
                "i10",
                "i20",
                "i30",
                "Tucson",
                "Santa Fe",
                "Creta",
                "Venue",
            ],
            "Isuzu": [
                "Trooper",
                "Rodeo",
                "D-Max",
                "MU-X",
                "KB",
                "Faster",
                "Gemini",
                "Hombre",
                "VehiCROSS",
                "Stylus",
            ],
            "JAC": [
                "T6",
                "T8",
                "Sunray",
                "Refine",
                "S2",
                "S3",
                "S5",
                "J3",
                "J5",
                "JS4",
            ],
            "Jeep": [
                "Wrangler",
                "Cherokee",
                "Grand Cherokee",
                "Compass",
                "Renegade",
                "Patriot",
                "Gladiator",
                "Wagoneer",
                "Liberty",
                "Commander",
            ],
            "Kia": [
                "Rio",
                "Cerato",
                "Optima",
                "Picanto",
                "Morning",
                "Soul",
                "Sportage",
                "Sorento",
                "Carens",
                "Carnival",
            ],
            "Mahindra": [
                "Scorpio",
                "Bolero",
                "Pik Up",
                "Thar",
                "XUV300",
                "XUV500",
                "XUV700",
                "KUV100",
                "Marazzo",
                "Quanto",
            ],
            "Mazda": [
                "2",
                "3",
                "6",
                "CX-3",
                "CX-30",
                "CX-5",
                "CX-7",
                "CX-9",
                "BT-50",
                "RX-8",
            ],
            "Mercedes-Benz": [
                "Clase A",
                "Clase B",
                "Clase C",
                "Clase E",
                "Clase S",
                "CLA",
                "GLA",
                "GLC",
                "GLE",
                "Sprinter",
            ],
            "MG": [
                "MG3",
                "MG5",
                "MG6",
                "MG GT",
                "ZS",
                "HS",
                "RX5",
                "Marvel R",
                "Hector",
                "One",
            ],
            "Mitsubishi": [
                "Lancer",
                "Galant",
                "Mirage",
                "Eclipse",
                "Outlander",
                "ASX",
                "Montero",
                "Montero Sport",
                "L200",
                "Xpander",
            ],
            "Nissan": [
                "Sunny",
                "Sentra",
                "Versa",
                "Tiida",
                "Almera",
                "March",
                "Altima",
                "X-Trail",
                "Pathfinder",
                "Navara",
            ],
            "Opel": [
                "Corsa",
                "Astra",
                "Vectra",
                "Kadett",
                "Mokka",
                "Insignia",
                "Meriva",
                "Zafira",
                "Combo",
                "Antara",
            ],
            "Peugeot": [
                "206",
                "207",
                "208",
                "301",
                "306",
                "307",
                "308",
                "405",
                "406",
                "508",
            ],
            "Renault": [
                "4",
                "5",
                "9",
                "11",
                "19",
                "Clio",
                "Mégane",
                "Symbol",
                "Koleos",
                "Duster",
            ],
            "SsangYong": [
                "Korando",
                "Musso",
                "Actyon",
                "Rexton",
                "Tivoli",
                "XLV",
                "Kyron",
                "Chairman",
                "Stavic",
                "Torres",
            ],
            "Subaru": [
                "Leone",
                "Justy",
                "Impreza",
                "Legacy",
                "Forester",
                "Outback",
                "XV",
                "WRX",
                "Baja",
                "BRZ",
            ],
            "Suzuki": [
                "Alto",
                "Celerio",
                "Baleno",
                "Swift",
                "Dzire",
                "Jimny",
                "Vitara",
                "Grand Vitara",
                "S-Cross",
                "Ertiga",
            ],
            "Toyota": [
                "Corolla",
                "Yaris",
                "Starlet",
                "Camry",
                "Avensis",
                "Hilux",
                "4Runner",
                "RAV4",
                "Prado",
                "Land Cruiser",
            ],
            "Volkswagen": [
                "Gol",
                "Voyage",
                "Polo",
                "Virtus",
                "Golf",
                "Bora",
                "Passat",
                "Tiguan",
                "Touareg",
                "Amarok",
            ],
        }

        self.stdout.write(self.style.SUCCESS("🇨🇱 Cargando marcas y modelos para Chile..."))

        total_marcas = 0
        total_modelos = 0

        for marca_nombre, modelos_lista in marcas_modelos_chile.items():
            # Obtener o crear la marca
            marca, created = Marca.objects.get_or_create(
                nombre=marca_nombre, country="CL", defaults={"country": "CL"}
            )

            if created:
                self.stdout.write(f"✅ Marca creada: {marca_nombre}")
            else:
                self.stdout.write(f"🔄 Marca existente: {marca_nombre}")

            # Eliminar modelos existentes para esta marca
            modelos_existentes = Modelo.objects.filter(marca=marca)
            if modelos_existentes.exists():
                self.stdout.write(
                    f"🗑️  Eliminando {modelos_existentes.count()} modelos existentes de {marca_nombre}"
                )
                modelos_existentes.delete()

            # Crear los nuevos modelos
            for modelo_nombre in modelos_lista:
                try:
                    Modelo.objects.create(nombre=modelo_nombre, marca=marca, country="CL")
                    self.stdout.write(f"   ✅ {modelo_nombre}")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"   ❌ Error creando {modelo_nombre}: {e}"))

            total_marcas += 1
            total_modelos += len(modelos_lista)

        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎉 Carga completada: {total_marcas} marcas, {total_modelos} modelos"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "✅ Base de datos actualizada con datos específicos del mercado chileno"
            )
        )
