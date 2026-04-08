"""
Management command para cargar marcas y modelos de vehÃƒÂ­culos por paÃƒÂ­s desde 1970 hasta la fecha.

Este comando carga marcas y modelos especÃƒÂ­ficos comercializados en cada paÃƒÂ­s,
respetando las diferencias de mercado entre paÃƒÂ­ses.

Uso:
    python manage.py cargar_marcas_modelos_por_pais --country CL
    python manage.py cargar_marcas_modelos_por_pais --country CO
    python manage.py cargar_marcas_modelos_por_pais --all
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.vehiculos import Vehiculo

from ._catalogo_marcas_modelos_latam import (
    BR_MARCAS_MODELOS,
    CO_MARCAS_MODELOS,
    EC_MARCAS_MODELOS,
    PE_MARCAS_MODELOS,
    VE_MARCAS_MODELOS,
)
from ._catalogo_marcas_modelos_mx import MX_MARCAS_MODELOS


# Datos de marcas y modelos por paÃƒÂ­s (desde 1970 hasta 2024)
MARCAS_MODELOS_POR_PAIS = {
    "CL": {
        # Chile - Marcas y modelos comercializados
        "Toyota": [
            "Corolla",
            "Camry",
            "RAV4",
            "Hilux",
            "Land Cruiser",
            "Yaris",
            "Prius",
            "Highlander",
            "Tacoma",
            "4Runner",
            "Sienna",
            "Tundra",
            "Sequoia",
            "C-HR",
            "Avalon",
            "Supra",
            "GR86",
            "bZ4X",
        ],
        "Chevrolet": [
            "Spark",
            "Sail",
            "Onix",
            "Prisma",
            "Cruze",
            "Malibu",
            "Equinox",
            "Traverse",
            "Tahoe",
            "Silverado",
            "Colorado",
            "Tracker",
            "Blazer",
        ],
        "Ford": [
            "Fiesta",
            "Focus",
            "Fusion",
            "Mustang",
            "Escape",
            "Explorer",
            "Edge",
            "Ranger",
            "F-150",
            "Bronco",
            "Maverick",
            "Expedition",
        ],
        "Nissan": [
            "Versa",
            "Sentra",
            "Altima",
            "Maxima",
            "Kicks",
            "Rogue",
            "Pathfinder",
            "Armada",
            "Frontier",
            "Titan",
            "X-Trail",
            "Murano",
            "Juke",
        ],
        "Hyundai": [
            "Accent",
            "Elantra",
            "Sonata",
            "Tucson",
            "Santa Fe",
            "Palisade",
            "Kona",
            "Venue",
            "Ioniq",
            "IONIQ 5",
            "IONIQ 6",
        ],
        "Kia": [
            "Rio",
            "Forte",
            "Optima",
            "Sorento",
            "Sportage",
            "Telluride",
            "Seltos",
            "Soul",
            "Niro",
            "EV6",
            "Carnival",
        ],
        "Mazda": ["Mazda2", "Mazda3", "Mazda6", "CX-3", "CX-5", "CX-9", "CX-30", "MX-5", "BT-50"],
        "Suzuki": ["Swift", "SX4", "Vitara", "Grand Vitara", "S-Cross", "Jimny", "XL7"],
        "Mitsubishi": ["Lancer", "Outlander", "Montero", "Pajero", "Eclipse Cross", "ASX"],
        "Honda": ["Fit", "Civic", "Accord", "CR-V", "Pilot", "HR-V", "Passport", "Ridgeline"],
        "Volkswagen": [
            "Polo",
            "Gol",
            "Vento",
            "Jetta",
            "Passat",
            "Tiguan",
            "Touareg",
            "Amarok",
            "T-Cross",
            "Nivus",
            "Taos",
        ],
        "Renault": ["Kwid", "Sandero", "Logan", "Duster", "Captur", "Koleos", "Oroch"],
        "Peugeot": ["208", "301", "308", "408", "2008", "3008", "5008", "Partner"],
        "CitroÃƒÂ«n": ["C3", "C4", "C5", "Berlingo", "C4 Cactus", "C4 Picasso"],
        "Fiat": ["Uno", "Palio", "Siena", "Strada", "Toro", "Ducato", "500", "Argo"],
        "Subaru": ["Impreza", "Legacy", "Outback", "Forester", "XV", "Ascent", "BRZ"],
        "Isuzu": ["D-Max", "MU-X", "NPR", "NQR"],
        "BMW": [
            "Serie 1",
            "Serie 2",
            "Serie 3",
            "Serie 4",
            "Serie 5",
            "Serie 7",
            "X1",
            "X2",
            "X3",
            "X4",
            "X5",
            "X6",
            "X7",
            "Z4",
            "iX",
            "i4",
        ],
        "Mercedes-Benz": [
            "Clase A",
            "Clase B",
            "Clase C",
            "Clase E",
            "Clase S",
            "GLA",
            "GLB",
            "GLC",
            "GLE",
            "GLS",
            "G-Class",
            "AMG GT",
        ],
        "Audi": [
            "A1",
            "A3",
            "A4",
            "A5",
            "A6",
            "A7",
            "A8",
            "Q2",
            "Q3",
            "Q5",
            "Q7",
            "Q8",
            "TT",
            "e-tron",
            "e-tron GT",
        ],
    },
    "MX": MX_MARCAS_MODELOS,
    "CO": {
        # Colombia - Marcas y modelos comercializados
        "Chevrolet": [
            "Spark",
            "Sail",
            "Onix",
            "Prisma",
            "Cruze",
            "Malibu",
            "Equinox",
            "Traverse",
            "Tahoe",
            "Silverado",
            "Colorado",
            "Tracker",
            "Blazer",
            "Aveo",
            "Optra",
            "Corsa",
            "Meriva",
            "Zafira",
        ],
        "Renault": [
            "Kwid",
            "Sandero",
            "Logan",
            "Duster",
            "Captur",
            "Koleos",
            "Oroch",
            "Symbol",
            "Fluence",
            "Megane",
            "Scenic",
        ],
        "Nissan": [
            "Versa",
            "Sentra",
            "Altima",
            "Kicks",
            "Rogue",
            "Pathfinder",
            "Frontier",
            "X-Trail",
            "Murano",
            "Juke",
            "March",
        ],
        "Mazda": ["Mazda2", "Mazda3", "Mazda6", "CX-3", "CX-5", "CX-9", "CX-30", "BT-50"],
        "Toyota": [
            "Corolla",
            "Camry",
            "RAV4",
            "Hilux",
            "Land Cruiser",
            "Yaris",
            "Prius",
            "Highlander",
            "Tacoma",
            "4Runner",
            "Sienna",
            "Tundra",
        ],
        "Hyundai": [
            "Accent",
            "Elantra",
            "Sonata",
            "Tucson",
            "Santa Fe",
            "Palisade",
            "Kona",
            "Venue",
            "i10",
            "i20",
            "i30",
        ],
        "Kia": [
            "Rio",
            "Forte",
            "Optima",
            "Sorento",
            "Sportage",
            "Telluride",
            "Seltos",
            "Soul",
            "Picanto",
        ],
        "Suzuki": ["Swift", "SX4", "Vitara", "Grand Vitara", "S-Cross", "Jimny"],
        "Mitsubishi": ["Lancer", "Outlander", "Montero", "Pajero", "Eclipse Cross", "ASX", "L200"],
        "Honda": ["Fit", "Civic", "Accord", "CR-V", "Pilot", "HR-V", "Passport"],
        "Volkswagen": [
            "Polo",
            "Gol",
            "Vento",
            "Jetta",
            "Passat",
            "Tiguan",
            "Touareg",
            "Amarok",
            "T-Cross",
            "Nivus",
        ],
        "Ford": [
            "Fiesta",
            "Focus",
            "Fusion",
            "Escape",
            "Explorer",
            "Edge",
            "Ranger",
            "F-150",
            "Bronco",
        ],
        "BMW": [
            "Serie 1",
            "Serie 2",
            "Serie 3",
            "Serie 4",
            "Serie 5",
            "Serie 7",
            "X1",
            "X2",
            "X3",
            "X4",
            "X5",
            "X6",
            "X7",
        ],
        "Mercedes-Benz": [
            "Clase A",
            "Clase B",
            "Clase C",
            "Clase E",
            "Clase S",
            "GLA",
            "GLB",
            "GLC",
            "GLE",
            "GLS",
            "G-Class",
        ],
        "Audi": ["A1", "A3", "A4", "A5", "A6", "A7", "A8", "Q2", "Q3", "Q5", "Q7", "Q8"],
    },
    "PE": {
        # PerÃƒÂº - Marcas y modelos comercializados
        "Toyota": [
            "Corolla",
            "Camry",
            "RAV4",
            "Hilux",
            "Land Cruiser",
            "Yaris",
            "Prius",
            "Highlander",
            "Tacoma",
            "4Runner",
            "Sienna",
            "Tundra",
            "Sequoia",
        ],
        "Nissan": [
            "Versa",
            "Sentra",
            "Altima",
            "Kicks",
            "Rogue",
            "Pathfinder",
            "Frontier",
            "X-Trail",
            "Murano",
            "Juke",
            "March",
        ],
        "Chevrolet": [
            "Spark",
            "Sail",
            "Onix",
            "Prisma",
            "Cruze",
            "Malibu",
            "Equinox",
            "Traverse",
            "Tahoe",
            "Silverado",
            "Colorado",
            "Tracker",
            "Blazer",
        ],
        "Hyundai": [
            "Accent",
            "Elantra",
            "Sonata",
            "Tucson",
            "Santa Fe",
            "Palisade",
            "Kona",
            "Venue",
            "i10",
            "i20",
        ],
        "Kia": [
            "Rio",
            "Forte",
            "Optima",
            "Sorento",
            "Sportage",
            "Telluride",
            "Seltos",
            "Soul",
            "Picanto",
        ],
        "Mazda": ["Mazda2", "Mazda3", "Mazda6", "CX-3", "CX-5", "CX-9", "CX-30", "BT-50"],
        "Suzuki": ["Swift", "SX4", "Vitara", "Grand Vitara", "S-Cross", "Jimny"],
        "Mitsubishi": ["Lancer", "Outlander", "Montero", "Pajero", "Eclipse Cross", "ASX", "L200"],
        "Honda": ["Fit", "Civic", "Accord", "CR-V", "Pilot", "HR-V", "Passport"],
        "Volkswagen": [
            "Polo",
            "Gol",
            "Vento",
            "Jetta",
            "Passat",
            "Tiguan",
            "Touareg",
            "Amarok",
            "T-Cross",
            "Nivus",
        ],
        "Renault": ["Kwid", "Sandero", "Logan", "Duster", "Captur", "Koleos", "Oroch"],
        "Peugeot": ["208", "301", "308", "408", "2008", "3008", "5008", "Partner"],
        "Fiat": ["Uno", "Palio", "Siena", "Strada", "Toro", "Ducato", "500", "Argo"],
        "BMW": [
            "Serie 1",
            "Serie 2",
            "Serie 3",
            "Serie 4",
            "Serie 5",
            "Serie 7",
            "X1",
            "X2",
            "X3",
            "X4",
            "X5",
            "X6",
            "X7",
        ],
        "Mercedes-Benz": [
            "Clase A",
            "Clase B",
            "Clase C",
            "Clase E",
            "Clase S",
            "GLA",
            "GLB",
            "GLC",
            "GLE",
            "GLS",
            "G-Class",
        ],
        "Audi": ["A1", "A3", "A4", "A5", "A6", "A7", "A8", "Q2", "Q3", "Q5", "Q7", "Q8"],
        "Ford": [
            "Fiesta",
            "Focus",
            "Fusion",
            "Escape",
            "Explorer",
            "Edge",
            "Ranger",
            "F-150",
            "Bronco",
        ],
        "Isuzu": ["D-Max", "MU-X", "NPR", "NQR"],
    },
    "EC": {
        # Ecuador - Marcas y modelos comercializados
        "Chevrolet": [
            "Spark",
            "Sail",
            "Onix",
            "Prisma",
            "Cruze",
            "Malibu",
            "Equinox",
            "Traverse",
            "Tahoe",
            "Silverado",
            "Colorado",
            "Tracker",
            "Blazer",
        ],
        "Toyota": [
            "Corolla",
            "Camry",
            "RAV4",
            "Hilux",
            "Land Cruiser",
            "Yaris",
            "Prius",
            "Highlander",
            "Tacoma",
            "4Runner",
            "Sienna",
            "Tundra",
        ],
        "Nissan": [
            "Versa",
            "Sentra",
            "Altima",
            "Kicks",
            "Rogue",
            "Pathfinder",
            "Frontier",
            "X-Trail",
            "Murano",
            "Juke",
            "March",
        ],
        "Hyundai": [
            "Accent",
            "Elantra",
            "Sonata",
            "Tucson",
            "Santa Fe",
            "Palisade",
            "Kona",
            "Venue",
            "i10",
            "i20",
        ],
        "Kia": [
            "Rio",
            "Forte",
            "Optima",
            "Sorento",
            "Sportage",
            "Telluride",
            "Seltos",
            "Soul",
            "Picanto",
        ],
        "Mazda": ["Mazda2", "Mazda3", "Mazda6", "CX-3", "CX-5", "CX-9", "CX-30", "BT-50"],
        "Suzuki": ["Swift", "SX4", "Vitara", "Grand Vitara", "S-Cross", "Jimny"],
        "Mitsubishi": ["Lancer", "Outlander", "Montero", "Pajero", "Eclipse Cross", "ASX", "L200"],
        "Honda": ["Fit", "Civic", "Accord", "CR-V", "Pilot", "HR-V", "Passport"],
        "Volkswagen": [
            "Polo",
            "Gol",
            "Vento",
            "Jetta",
            "Passat",
            "Tiguan",
            "Touareg",
            "Amarok",
            "T-Cross",
            "Nivus",
        ],
        "Renault": ["Kwid", "Sandero", "Logan", "Duster", "Captur", "Koleos", "Oroch"],
        "Ford": [
            "Fiesta",
            "Focus",
            "Fusion",
            "Escape",
            "Explorer",
            "Edge",
            "Ranger",
            "F-150",
            "Bronco",
        ],
        "BMW": [
            "Serie 1",
            "Serie 2",
            "Serie 3",
            "Serie 4",
            "Serie 5",
            "Serie 7",
            "X1",
            "X2",
            "X3",
            "X4",
            "X5",
            "X6",
            "X7",
        ],
        "Mercedes-Benz": [
            "Clase A",
            "Clase B",
            "Clase C",
            "Clase E",
            "Clase S",
            "GLA",
            "GLB",
            "GLC",
            "GLE",
            "GLS",
            "G-Class",
        ],
        "Audi": ["A1", "A3", "A4", "A5", "A6", "A7", "A8", "Q2", "Q3", "Q5", "Q7", "Q8"],
    },
    "BR": {
        # Brasil - Marcas y modelos comercializados
        "Volkswagen": [
            "Gol",
            "Polo",
            "Virtus",
            "Jetta",
            "Passat",
            "Tiguan",
            "Touareg",
            "Amarok",
            "T-Cross",
            "Nivus",
            "Saveiro",
            "Kombi",
            "Fox",
            "Up!",
        ],
        "Fiat": [
            "Uno",
            "Palio",
            "Siena",
            "Strada",
            "Toro",
            "Ducato",
            "500",
            "Argo",
            "Mobi",
            "Cronos",
            "Fiorino",
            "Doblo",
            "Bravo",
            "Linea",
        ],
        "Chevrolet": [
            "Onix",
            "Prisma",
            "Cruze",
            "Malibu",
            "Equinox",
            "Traverse",
            "Silverado",
            "Colorado",
            "Tracker",
            "Blazer",
            "Spin",
            "Montana",
            "S10",
            "Celta",
            "Corsa",
            "Meriva",
            "Zafira",
        ],
        "Ford": [
            "Ka",
            "Fiesta",
            "Focus",
            "Fusion",
            "EcoSport",
            "Edge",
            "Ranger",
            "F-150",
            "Bronco",
            "Territory",
            "Maverick",
        ],
        "Toyota": [
            "Corolla",
            "Camry",
            "RAV4",
            "Hilux",
            "Land Cruiser",
            "Yaris",
            "Prius",
            "Highlander",
            "Tacoma",
            "4Runner",
            "Sienna",
            "Tundra",
            "SW4",
        ],
        "Renault": [
            "Kwid",
            "Sandero",
            "Logan",
            "Duster",
            "Captur",
            "Koleos",
            "Oroch",
            "Fluence",
            "Megane",
            "Scenic",
            "Kangoo",
        ],
        "Hyundai": [
            "HB20",
            "HB20S",
            "HB20X",
            "Creta",
            "Tucson",
            "Santa Fe",
            "Palisade",
            "iX35",
            "Azera",
            "Elantra",
            "Sonata",
        ],
        "Honda": ["Fit", "City", "Civic", "Accord", "CR-V", "HR-V", "WR-V"],
        "Nissan": ["Versa", "Sentra", "Kicks", "Rogue", "Frontier", "X-Trail", "March"],
        "Jeep": ["Renegade", "Compass", "Commander", "Grand Cherokee", "Wrangler"],
        "Peugeot": ["208", "2008", "3008", "5008", "Partner", "Expert"],
        "CitroÃƒÂ«n": ["C3", "C4", "C4 Cactus", "C4 Picasso", "Berlingo", "Jumper"],
        "BMW": [
            "Serie 1",
            "Serie 2",
            "Serie 3",
            "Serie 4",
            "Serie 5",
            "Serie 7",
            "X1",
            "X2",
            "X3",
            "X4",
            "X5",
            "X6",
            "X7",
        ],
        "Mercedes-Benz": [
            "Clase A",
            "Clase B",
            "Clase C",
            "Clase E",
            "Clase S",
            "GLA",
            "GLB",
            "GLC",
            "GLE",
            "GLS",
            "G-Class",
            "Sprinter",
        ],
        "Audi": ["A1", "A3", "A4", "A5", "A6", "A7", "A8", "Q2", "Q3", "Q5", "Q7", "Q8"],
    },
    "VE": {
        # Venezuela - Marcas y modelos comercializados
        "Chevrolet": [
            "Spark",
            "Sail",
            "Onix",
            "Prisma",
            "Cruze",
            "Malibu",
            "Equinox",
            "Traverse",
            "Tahoe",
            "Silverado",
            "Colorado",
            "Tracker",
            "Blazer",
            "Aveo",
            "Optra",
            "Corsa",
            "Meriva",
            "Zafira",
            "Cavalier",
        ],
        "Ford": [
            "Fiesta",
            "Focus",
            "Fusion",
            "Escape",
            "Explorer",
            "Edge",
            "Ranger",
            "F-150",
            "Bronco",
            "EcoSport",
        ],
        "Toyota": [
            "Corolla",
            "Camry",
            "RAV4",
            "Hilux",
            "Land Cruiser",
            "Yaris",
            "Prius",
            "Highlander",
            "Tacoma",
            "4Runner",
            "Sienna",
            "Tundra",
        ],
        "Nissan": [
            "Versa",
            "Sentra",
            "Altima",
            "Kicks",
            "Rogue",
            "Pathfinder",
            "Frontier",
            "X-Trail",
            "Murano",
            "Juke",
            "March",
        ],
        "Hyundai": [
            "Accent",
            "Elantra",
            "Sonata",
            "Tucson",
            "Santa Fe",
            "Palisade",
            "Kona",
            "Venue",
            "i10",
            "i20",
        ],
        "Kia": [
            "Rio",
            "Forte",
            "Optima",
            "Sorento",
            "Sportage",
            "Telluride",
            "Seltos",
            "Soul",
            "Picanto",
        ],
        "Mazda": ["Mazda2", "Mazda3", "Mazda6", "CX-3", "CX-5", "CX-9", "CX-30", "BT-50"],
        "Suzuki": ["Swift", "SX4", "Vitara", "Grand Vitara", "S-Cross", "Jimny"],
        "Mitsubishi": ["Lancer", "Outlander", "Montero", "Pajero", "Eclipse Cross", "ASX", "L200"],
        "Honda": ["Fit", "Civic", "Accord", "CR-V", "Pilot", "HR-V", "Passport"],
        "Volkswagen": [
            "Polo",
            "Gol",
            "Vento",
            "Jetta",
            "Passat",
            "Tiguan",
            "Touareg",
            "Amarok",
            "T-Cross",
            "Nivus",
        ],
        "Renault": ["Kwid", "Sandero", "Logan", "Duster", "Captur", "Koleos", "Oroch"],
        "Peugeot": ["208", "301", "308", "408", "2008", "3008", "5008", "Partner"],
        "BMW": [
            "Serie 1",
            "Serie 2",
            "Serie 3",
            "Serie 4",
            "Serie 5",
            "Serie 7",
            "X1",
            "X2",
            "X3",
            "X4",
            "X5",
            "X6",
            "X7",
        ],
        "Mercedes-Benz": [
            "Clase A",
            "Clase B",
            "Clase C",
            "Clase E",
            "Clase S",
            "GLA",
            "GLB",
            "GLC",
            "GLE",
            "GLS",
            "G-Class",
        ],
        "Audi": ["A1", "A3", "A4", "A5", "A6", "A7", "A8", "Q2", "Q3", "Q5", "Q7", "Q8"],
    },
}

MARCAS_MODELOS_POR_PAIS.update(
    {
        "CO": CO_MARCAS_MODELOS,
        "PE": PE_MARCAS_MODELOS,
        "EC": EC_MARCAS_MODELOS,
        "VE": VE_MARCAS_MODELOS,
        "BR": BR_MARCAS_MODELOS,
    }
)


class Command(BaseCommand):
    help = "Carga marcas y modelos de vehÃƒÂ­culos por paÃƒÂ­s desde 1970 hasta la fecha"

    def add_arguments(self, parser):
        parser.add_argument(
            "--country",
            type=str,
            help="CÃƒÂ³digo de paÃƒÂ­s (CL, US, MX, PE, CO, EC, BR, VE). Si no se especifica, se cargan todos.",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Cargar marcas y modelos para todos los paÃƒÂ­ses",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simular la carga sin guardar en la base de datos",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Sincronizar el catalogo con el seed y eliminar sobrantes que no esten en uso.",
        )

    def handle(self, *args, **options):
        countries_to_process = []

        if options["all"]:
            countries_to_process = list(MARCAS_MODELOS_POR_PAIS.keys())
        elif options["country"]:
            country = options["country"].upper()
            if country not in MARCAS_MODELOS_POR_PAIS:
                self.stdout.write(
                    self.style.ERROR(
                        f"PaÃƒÂ­s '{country}' no estÃƒÂ¡ soportado. PaÃƒÂ­ses disponibles: {', '.join(MARCAS_MODELOS_POR_PAIS.keys())}"
                    )
                )
                return
            countries_to_process = [country]
        else:
            self.stdout.write(
                self.style.ERROR(
                    "Debe especificar --country <CODIGO> o --all para cargar todos los paÃƒÂ­ses"
                )
            )
            return

        dry_run = options["dry_run"]
        replace = options["replace"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY-RUN: no se guardaran cambios"))

        total_marcas_creadas = 0
        total_modelos_creados = 0

        for country in countries_to_process:
            self.stdout.write(
                self.style.SUCCESS(f"\n{'='*60}\nProcesando pais: {country}\n{'='*60}")
            )

            marcas_modelos = MARCAS_MODELOS_POR_PAIS.get(country, {})

            if not marcas_modelos:
                self.stdout.write(self.style.WARNING(f"No hay datos para el pais {country}"))
                continue

            marcas_creadas = 0
            modelos_creados = 0
            modelos_eliminados = 0
            marcas_eliminadas = 0

            with transaction.atomic():
                if replace:
                    stale_models_result = self._delete_stale_models(
                        country, marcas_modelos, dry_run
                    )
                    modelos_eliminados = stale_models_result["deleted"]

                for marca_nombre, modelos_list in marcas_modelos.items():
                    # Crear o obtener marca
                    marca, marca_created = Marca.objects.get_or_create(
                        nombre=marca_nombre,
                        country=country,
                        defaults={"nombre": marca_nombre, "country": country},
                    )

                    if marca_created:
                        marcas_creadas += 1
                        if not dry_run:
                            self.stdout.write(
                                self.style.SUCCESS(f"  OK marca creada: {marca_nombre}")
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(f"  [DRY-RUN] Marca a crear: {marca_nombre}")
                            )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"  INFO marca ya existe: {marca_nombre}")
                        )

                    # Crear modelos para esta marca
                    for modelo_nombre in modelos_list:
                        try:
                            modelo, modelo_created = Modelo.objects.get_or_create(
                                nombre=modelo_nombre,
                                marca=marca,
                                country=country,
                                defaults={
                                    "nombre": modelo_nombre,
                                    "marca": marca,
                                    "country": country,
                                },
                            )

                            if modelo_created:
                                modelos_creados += 1
                                if not dry_run:
                                    self.stdout.write(
                                        self.style.SUCCESS(
                                            f"    OK modelo creado: {marca_nombre} {modelo_nombre}"
                                        )
                                    )
                                else:
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f"    [DRY-RUN] Modelo a crear: {marca_nombre} {modelo_nombre}"
                                        )
                                    )
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(
                                    f"    ERROR creando modelo {modelo_nombre} para {marca_nombre}: {e}"
                                )
                            )

                if replace:
                    stale_brands_result = self._delete_stale_brands(
                        country, marcas_modelos, dry_run
                    )
                    marcas_eliminadas = stale_brands_result["deleted"]

                if dry_run:
                    transaction.set_rollback(True)
                    self.stdout.write(
                        self.style.WARNING(
                            f"\n[DRY-RUN] Se crearian {marcas_creadas} marcas, {modelos_creados} modelos, se eliminarian {modelos_eliminados} modelos y {marcas_eliminadas} marcas para {country}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"\nPais {country}: {marcas_creadas} marcas, {modelos_creados} modelos creados, {modelos_eliminados} modelos y {marcas_eliminadas} marcas eliminados"
                        )
                    )

            total_marcas_creadas += marcas_creadas
            total_modelos_creados += modelos_creados

        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'='*60}\nRESUMEN TOTAL\n{'='*60}\n"
                f"Marcas creadas: {total_marcas_creadas}\n"
                f"Modelos creados: {total_modelos_creados}\n"
                f"Paises procesados: {len(countries_to_process)}\n"
            )
        )

    def _delete_stale_models(self, country, marcas_modelos, dry_run):
        desired_models_by_brand = {
            marca_nombre: set(modelos_list) for marca_nombre, modelos_list in marcas_modelos.items()
        }
        deleted = 0
        skipped = 0

        for modelo in (
            Modelo.objects.filter(country=country)
            .select_related("marca")
            .order_by("marca__nombre", "nombre")
        ):
            desired_models = desired_models_by_brand.get(modelo.marca.nombre)
            if desired_models and modelo.nombre in desired_models:
                continue

            if Vehiculo.objects.filter(modelo=modelo).exists():
                skipped += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"    WARNING modelo en uso, no se elimina: {modelo.marca.nombre} {modelo.nombre}"
                    )
                )
                continue

            deleted += 1
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"    [DRY-RUN] Modelo a eliminar: {modelo.marca.nombre} {modelo.nombre}"
                    )
                )
            else:
                modelo.delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"    OK modelo eliminado: {modelo.marca.nombre} {modelo.nombre}"
                    )
                )

        if skipped:
            self.stdout.write(
                self.style.WARNING(
                    f"    INFO {skipped} modelo(s) sobrantes quedaron intactos por estar referenciados."
                )
            )

        return {"deleted": deleted, "skipped": skipped}

    def _delete_stale_brands(self, country, marcas_modelos, dry_run):
        desired_brands = set(marcas_modelos.keys())
        deleted = 0

        for marca in Marca.objects.filter(country=country).order_by("nombre"):
            if marca.nombre in desired_brands:
                continue

            if Modelo.objects.filter(marca=marca).exists():
                continue

            if Vehiculo.objects.filter(marca=marca).exists():
                self.stdout.write(
                    self.style.WARNING(f"    WARNING marca en uso, no se elimina: {marca.nombre}")
                )
                continue

            deleted += 1
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f"    [DRY-RUN] Marca a eliminar: {marca.nombre}")
                )
            else:
                marca.delete()
                self.stdout.write(self.style.SUCCESS(f"    OK marca eliminada: {marca.nombre}"))

        return {"deleted": deleted}
