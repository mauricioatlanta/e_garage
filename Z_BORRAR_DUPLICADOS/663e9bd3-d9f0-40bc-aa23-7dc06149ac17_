"""
Comando para cargar estados y ciudades principales de México
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from taller.models.ubicacion import Ciudad, Estado


class Command(BaseCommand):
    help = "Carga los 32 estados de México y ciudades principales en la base de datos"

    def handle(self, *args, **options):
        self.stdout.write("[MX] Cargando estados de México...")

        estados_mexico = [
            {"codigo": "AG", "nombre": "Aguascalientes", "timezone": "America/Mexico_City"},
            {"codigo": "BC", "nombre": "Baja California", "timezone": "America/Tijuana"},
            {"codigo": "BS", "nombre": "Baja California Sur", "timezone": "America/Mazatlan"},
            {"codigo": "CM", "nombre": "Campeche", "timezone": "America/Mexico_City"},
            {"codigo": "CO", "nombre": "Coahuila", "timezone": "America/Monterrey"},
            {"codigo": "CL", "nombre": "Colima", "timezone": "America/Mexico_City"},
            {"codigo": "CS", "nombre": "Chiapas", "timezone": "America/Mexico_City"},
            {"codigo": "CH", "nombre": "Chihuahua", "timezone": "America/Chihuahua"},
            {"codigo": "CX", "nombre": "Ciudad de México", "timezone": "America/Mexico_City"},
            {"codigo": "DG", "nombre": "Durango", "timezone": "America/Monterrey"},
            {"codigo": "GT", "nombre": "Guanajuato", "timezone": "America/Mexico_City"},
            {"codigo": "GR", "nombre": "Guerrero", "timezone": "America/Mexico_City"},
            {"codigo": "HG", "nombre": "Hidalgo", "timezone": "America/Mexico_City"},
            {"codigo": "JA", "nombre": "Jalisco", "timezone": "America/Mexico_City"},
            {"codigo": "ME", "nombre": "Estado de México", "timezone": "America/Mexico_City"},
            {"codigo": "MI", "nombre": "Michoacán", "timezone": "America/Mexico_City"},
            {"codigo": "MO", "nombre": "Morelos", "timezone": "America/Mexico_City"},
            {"codigo": "NA", "nombre": "Nayarit", "timezone": "America/Mazatlan"},
            {"codigo": "NL", "nombre": "Nuevo León", "timezone": "America/Monterrey"},
            {"codigo": "OA", "nombre": "Oaxaca", "timezone": "America/Mexico_City"},
            {"codigo": "PU", "nombre": "Puebla", "timezone": "America/Mexico_City"},
            {"codigo": "QE", "nombre": "Querétaro", "timezone": "America/Mexico_City"},
            {"codigo": "QR", "nombre": "Quintana Roo", "timezone": "America/Cancun"},
            {"codigo": "SL", "nombre": "San Luis Potosí", "timezone": "America/Mexico_City"},
            {"codigo": "SI", "nombre": "Sinaloa", "timezone": "America/Mazatlan"},
            {"codigo": "SO", "nombre": "Sonora", "timezone": "America/Hermosillo"},
            {"codigo": "TB", "nombre": "Tabasco", "timezone": "America/Mexico_City"},
            {"codigo": "TM", "nombre": "Tamaulipas", "timezone": "America/Monterrey"},
            {"codigo": "TL", "nombre": "Tlaxcala", "timezone": "America/Mexico_City"},
            {"codigo": "VE", "nombre": "Veracruz", "timezone": "America/Mexico_City"},
            {"codigo": "YU", "nombre": "Yucatán", "timezone": "America/Merida"},
            {"codigo": "ZA", "nombre": "Zacatecas", "timezone": "America/Mexico_City"},
        ]

        estados_creados = 0
        for estado_data in estados_mexico:
            estado, created = Estado.objects.get_or_create(
                codigo=estado_data["codigo"],
                pais="MX",
                defaults={
                    "nombre": estado_data["nombre"],
                    "sales_tax": Decimal("16.00"),
                    "timezone": estado_data["timezone"],
                },
            )

            if created:
                estados_creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  [OK] {estado_data['nombre']} ({estado_data['codigo']})")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"  [EXISTE] {estado_data['nombre']} ({estado_data['codigo']}) ya existe"
                    )
                )

        self.stdout.write("")
        self.stdout.write(f"Estados creados: {estados_creados}/{len(estados_mexico)}")

        self.stdout.write("")
        self.stdout.write("[CIUDADES] Cargando ciudades principales de México...")

        ciudades_mexico = [
            {"nombre": "Aguascalientes", "estado": "AG", "poblacion": 934000, "es_capital": True},
            {"nombre": "Tijuana", "estado": "BC", "poblacion": 1987000, "es_capital": False},
            {"nombre": "Mexicali", "estado": "BC", "poblacion": 1094000, "es_capital": True},
            {"nombre": "La Paz", "estado": "BS", "poblacion": 292000, "es_capital": True},
            {
                "nombre": "San José del Cabo",
                "estado": "BS",
                "poblacion": 136000,
                "es_capital": False,
            },
            {"nombre": "Campeche", "estado": "CM", "poblacion": 294000, "es_capital": True},
            {"nombre": "Saltillo", "estado": "CO", "poblacion": 879000, "es_capital": True},
            {"nombre": "Torreón", "estado": "CO", "poblacion": 735000, "es_capital": False},
            {"nombre": "Colima", "estado": "CL", "poblacion": 330000, "es_capital": True},
            {"nombre": "Manzanillo", "estado": "CL", "poblacion": 191000, "es_capital": False},
            {"nombre": "Tuxtla Gutiérrez", "estado": "CS", "poblacion": 598000, "es_capital": True},
            {
                "nombre": "San Cristóbal de las Casas",
                "estado": "CS",
                "poblacion": 215000,
                "es_capital": False,
            },
            {"nombre": "Chihuahua", "estado": "CH", "poblacion": 925000, "es_capital": True},
            {"nombre": "Ciudad Juárez", "estado": "CH", "poblacion": 1500000, "es_capital": False},
            {"nombre": "Coyoacán", "estado": "CX", "poblacion": 620000, "es_capital": False},
            {"nombre": "Cuauhtémoc", "estado": "CX", "poblacion": 545000, "es_capital": False},
            {"nombre": "Durango", "estado": "DG", "poblacion": 690000, "es_capital": True},
            {"nombre": "Gómez Palacio", "estado": "DG", "poblacion": 342000, "es_capital": False},
            {"nombre": "León", "estado": "GT", "poblacion": 1730000, "es_capital": False},
            {"nombre": "Guanajuato", "estado": "GT", "poblacion": 198000, "es_capital": True},
            {"nombre": "Acapulco", "estado": "GR", "poblacion": 858000, "es_capital": False},
            {"nombre": "Chilpancingo", "estado": "GR", "poblacion": 240000, "es_capital": True},
            {"nombre": "Pachuca", "estado": "HG", "poblacion": 314000, "es_capital": True},
            {"nombre": "Guadalajara", "estado": "JA", "poblacion": 1530000, "es_capital": True},
            {"nombre": "Zapopan", "estado": "JA", "poblacion": 1410000, "es_capital": False},
            {"nombre": "Toluca", "estado": "ME", "poblacion": 910000, "es_capital": True},
            {"nombre": "Ecatepec", "estado": "ME", "poblacion": 1670000, "es_capital": False},
            {"nombre": "Morelia", "estado": "MI", "poblacion": 849000, "es_capital": True},
            {"nombre": "Uruapan", "estado": "MI", "poblacion": 356000, "es_capital": False},
            {"nombre": "Cuernavaca", "estado": "MO", "poblacion": 366000, "es_capital": True},
            {"nombre": "Tepic", "estado": "NA", "poblacion": 534000, "es_capital": True},
            {"nombre": "Monterrey", "estado": "NL", "poblacion": 1130000, "es_capital": True},
            {
                "nombre": "San Pedro Garza García",
                "estado": "NL",
                "poblacion": 123000,
                "es_capital": False,
            },
            {"nombre": "Oaxaca de Juárez", "estado": "OA", "poblacion": 300000, "es_capital": True},
            {"nombre": "Puebla", "estado": "PU", "poblacion": 1700000, "es_capital": True},
            {"nombre": "Querétaro", "estado": "QE", "poblacion": 1130000, "es_capital": True},
            {"nombre": "Cancún", "estado": "QR", "poblacion": 888000, "es_capital": False},
            {"nombre": "Chetumal", "estado": "QR", "poblacion": 169000, "es_capital": True},
            {"nombre": "San Luis Potosí", "estado": "SL", "poblacion": 936000, "es_capital": True},
            {"nombre": "Culiacán", "estado": "SI", "poblacion": 1040000, "es_capital": True},
            {"nombre": "Mazatlán", "estado": "SI", "poblacion": 502000, "es_capital": False},
            {"nombre": "Hermosillo", "estado": "SO", "poblacion": 936000, "es_capital": True},
            {"nombre": "Ciudad Obregón", "estado": "SO", "poblacion": 436000, "es_capital": False},
            {"nombre": "Villahermosa", "estado": "TB", "poblacion": 859000, "es_capital": True},
            {"nombre": "Tampico", "estado": "TM", "poblacion": 314000, "es_capital": False},
            {"nombre": "Ciudad Victoria", "estado": "TM", "poblacion": 365000, "es_capital": True},
            {"nombre": "Tlaxcala", "estado": "TL", "poblacion": 138000, "es_capital": True},
            {"nombre": "Xalapa", "estado": "VE", "poblacion": 488000, "es_capital": True},
            {"nombre": "Veracruz", "estado": "VE", "poblacion": 609000, "es_capital": False},
            {"nombre": "Mérida", "estado": "YU", "poblacion": 995000, "es_capital": True},
            {"nombre": "Valladolid", "estado": "YU", "poblacion": 105000, "es_capital": False},
            {"nombre": "Zacatecas", "estado": "ZA", "poblacion": 140000, "es_capital": True},
            {"nombre": "Fresnillo", "estado": "ZA", "poblacion": 240000, "es_capital": False},
        ]

        ciudades_creadas = 0
        for ciudad_data in ciudades_mexico:
            try:
                estado = Estado.objects.get(codigo=ciudad_data["estado"], pais="MX")
                ciudad, created = Ciudad.objects.get_or_create(
                    nombre=ciudad_data["nombre"],
                    estado=estado,
                    defaults={
                        "poblacion": ciudad_data["poblacion"],
                        "es_capital": ciudad_data["es_capital"],
                        "sales_tax_local": Decimal("0.00"),
                    },
                )

                if created:
                    ciudades_creadas += 1
                    capital = "[CAPITAL]" if ciudad_data["es_capital"] else "[CIUDAD] "
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  {capital} {ciudad_data['nombre']}, {ciudad_data['estado']}"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  [EXISTE] {ciudad_data['nombre']}, {ciudad_data['estado']} ya existe"
                        )
                    )
            except Estado.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"  [ERROR] Estado {ciudad_data['estado']} no encontrado para {ciudad_data['nombre']}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(f"Ciudades creadas: {ciudades_creadas}/{len(ciudades_mexico)}")
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("[MX] Estados y ciudades de México cargados exitosamente!")
        )
