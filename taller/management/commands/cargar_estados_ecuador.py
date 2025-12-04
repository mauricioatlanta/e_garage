"""
Comando para cargar las 24 provincias de Ecuador y sus principales ciudades
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from taller.models.ubicacion import Ciudad, Estado


class Command(BaseCommand):
    help = "Carga las 24 provincias de Ecuador y principales ciudades en la base de datos"

    def handle(self, *args, **options):
        self.stdout.write("[EC] Cargando provincias de Ecuador...")

        # 24 provincias de Ecuador con IVA 12%
        # Códigos ISO 3166-2:EC (simplificados)
        provincias_ecuador = [
            {
                "codigo": "P",
                "nombre": "Pichincha",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Quito", "es_capital": True, "poblacion": 2011388},
                    {"nombre": "Cayambe", "poblacion": 85795},
                    {"nombre": "Machachi", "poblacion": 35000},
                    {"nombre": "Sangolquí", "poblacion": 94000},
                ],
            },
            {
                "codigo": "G",
                "nombre": "Guayas",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Guayaquil", "es_capital": True, "poblacion": 2698077},
                    {"nombre": "Durán", "poblacion": 315724},
                    {"nombre": "Milagro", "poblacion": 199835},
                    {"nombre": "Daule", "poblacion": 133178},
                ],
            },
            {
                "codigo": "A",
                "nombre": "Azuay",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Cuenca", "es_capital": True, "poblacion": 505585},
                    {"nombre": "Gualaceo", "poblacion": 51587},
                ],
            },
            {
                "codigo": "B",
                "nombre": "Bolívar",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Guaranda", "es_capital": True, "poblacion": 92592},
                ],
            },
            {
                "codigo": "C",
                "nombre": "Carchi",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Tulcán", "es_capital": True, "poblacion": 94560},
                ],
            },
            {
                "codigo": "F",
                "nombre": "Cañar",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Azogues", "es_capital": True, "poblacion": 70064},
                    {"nombre": "Cañar", "poblacion": 58185},
                ],
            },
            {
                "codigo": "H",
                "nombre": "Chimborazo",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Riobamba", "es_capital": True, "poblacion": 225741},
                    {"nombre": "Alausí", "poblacion": 44930},
                ],
            },
            {
                "codigo": "X",
                "nombre": "Cotopaxi",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Latacunga", "es_capital": True, "poblacion": 170489},
                    {"nombre": "La Maná", "poblacion": 50000},
                ],
            },
            {
                "codigo": "O",
                "nombre": "El Oro",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Machala", "es_capital": True, "poblacion": 289141},
                    {"nombre": "Pasaje", "poblacion": 82851},
                    {"nombre": "Huaquillas", "poblacion": 53587},
                ],
            },
            {
                "codigo": "E",
                "nombre": "Esmeraldas",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Esmeraldas", "es_capital": True, "poblacion": 189504},
                ],
            },
            {
                "codigo": "W",
                "nombre": "Galápagos",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Puerto Baquerizo Moreno", "es_capital": True, "poblacion": 6672},
                    {"nombre": "Puerto Ayora", "poblacion": 11974},
                ],
            },
            {
                "codigo": "I",
                "nombre": "Imbabura",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Ibarra", "es_capital": True, "poblacion": 181175},
                    {"nombre": "Otavalo", "poblacion": 110461},
                ],
            },
            {
                "codigo": "L",
                "nombre": "Loja",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Loja", "es_capital": True, "poblacion": 214855},
                    {"nombre": "Catamayo", "poblacion": 32315},
                ],
            },
            {
                "codigo": "R",
                "nombre": "Los Ríos",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Babahoyo", "es_capital": True, "poblacion": 153776},
                    {"nombre": "Quevedo", "poblacion": 213842},
                    {"nombre": "Ventanas", "poblacion": 80659},
                ],
            },
            {
                "codigo": "M",
                "nombre": "Manabí",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Portoviejo", "es_capital": True, "poblacion": 321817},
                    {"nombre": "Manta", "poblacion": 264281},
                    {"nombre": "Chone", "poblacion": 126017},
                ],
            },
            {
                "codigo": "S",
                "nombre": "Morona Santiago",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Macas", "es_capital": True, "poblacion": 40641},
                ],
            },
            {
                "codigo": "N",
                "nombre": "Napo",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Tena", "es_capital": True, "poblacion": 60880},
                ],
            },
            {
                "codigo": "D",
                "nombre": "Orellana",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {
                        "nombre": "Puerto Francisco de Orellana",
                        "es_capital": True,
                        "poblacion": 72795,
                    },
                ],
            },
            {
                "codigo": "Y",
                "nombre": "Pastaza",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Puyo", "es_capital": True, "poblacion": 33557},
                ],
            },
            {
                "codigo": "SE",
                "nombre": "Santa Elena",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Santa Elena", "es_capital": True, "poblacion": 144076},
                    {"nombre": "Salinas", "poblacion": 68675},
                    {"nombre": "La Libertad", "poblacion": 115688},
                ],
            },
            {
                "codigo": "SD",
                "nombre": "Santo Domingo de los Tsáchilas",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Santo Domingo", "es_capital": True, "poblacion": 368013},
                ],
            },
            {
                "codigo": "U",
                "nombre": "Sucumbíos",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Nueva Loja", "es_capital": True, "poblacion": 57727},
                ],
            },
            {
                "codigo": "T",
                "nombre": "Tungurahua",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Ambato", "es_capital": True, "poblacion": 387309},
                    {"nombre": "Baños de Agua Santa", "poblacion": 21167},
                ],
            },
            {
                "codigo": "Z",
                "nombre": "Zamora Chinchipe",
                "timezone": "America/Guayaquil",
                "sales_tax": Decimal("12.00"),
                "ciudades": [
                    {"nombre": "Zamora", "es_capital": True, "poblacion": 15276},
                ],
            },
        ]

        estados_creados = 0
        estados_actualizados = 0
        ciudades_creadas = 0
        ciudades_existentes = 0

        for provincia_data in provincias_ecuador:
            # Crear o actualizar provincia
            estado, created = Estado.objects.update_or_create(
                pais="EC",
                codigo=provincia_data["codigo"],
                defaults={
                    "nombre": provincia_data["nombre"],
                    "sales_tax": provincia_data["sales_tax"],
                    "timezone": provincia_data["timezone"],
                },
            )

            if created:
                estados_creados += 1
                self.stdout.write(f"  ✅ Creada provincia: {estado.nombre} ({estado.codigo})")
            else:
                estados_actualizados += 1
                self.stdout.write(f"  🔄 Actualizada provincia: {estado.nombre} ({estado.codigo})")

            # Crear ciudades
            for ciudad_data in provincia_data["ciudades"]:
                ciudad, created = Ciudad.objects.get_or_create(
                    estado=estado,
                    nombre=ciudad_data["nombre"],
                    defaults={
                        "poblacion": ciudad_data.get("poblacion"),
                        "es_capital": ciudad_data.get("es_capital", False),
                    },
                )

                if created:
                    ciudades_creadas += 1
                    capital_mark = " 🏛️ " if ciudad.es_capital else ""
                    self.stdout.write(f"    ➕ {capital_mark}{ciudad.nombre}")
                else:
                    ciudades_existentes += 1

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Carga completada para Ecuador:\n"
                f"   • Provincias creadas: {estados_creados}\n"
                f"   • Provincias actualizadas: {estados_actualizados}\n"
                f"   • Ciudades nuevas: {ciudades_creadas}\n"
                f"   • Ciudades existentes: {ciudades_existentes}\n"
                f"   • Total provincias: {Estado.objects.filter(pais='EC').count()}\n"
                f"   • Total ciudades: {Ciudad.objects.filter(estado__pais='EC').count()}"
            )
        )
