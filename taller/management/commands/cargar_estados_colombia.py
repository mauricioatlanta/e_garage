"""
Comando para cargar los 33 departamentos de Colombia y sus principales ciudades
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from taller.models.ubicacion import Ciudad, Estado


class Command(BaseCommand):
    help = "Carga los 33 departamentos de Colombia y principales ciudades en la base de datos"

    def handle(self, *args, **options):
        self.stdout.write("[CO] Cargando departamentos de Colombia...")

        # 33 departamentos de Colombia con IVA 19%
        # Códigos ISO 3166-2:CO
        departamentos_colombia = [
            {
                "codigo": "DC",
                "nombre": "Distrito Capital de Bogotá",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Bogotá", "es_capital": True, "poblacion": 7181469},
                ],
            },
            {
                "codigo": "ANT",
                "nombre": "Antioquia",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Medellín", "es_capital": True, "poblacion": 2569007},
                    {"nombre": "Bello", "poblacion": 506167},
                    {"nombre": "Itagüí", "poblacion": 281853},
                    {"nombre": "Envigado", "poblacion": 246622},
                    {"nombre": "Rionegro", "poblacion": 126759},
                    {"nombre": "Apartadó", "poblacion": 195237},
                ],
            },
            {
                "codigo": "ATL",
                "nombre": "Atlántico",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Barranquilla", "es_capital": True, "poblacion": 1274250},
                    {"nombre": "Soledad", "poblacion": 680755},
                    {"nombre": "Malambo", "poblacion": 141351},
                    {"nombre": "Sabanalarga", "poblacion": 109432},
                ],
            },
            {
                "codigo": "BOL",
                "nombre": "Bolívar",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Cartagena", "es_capital": True, "poblacion": 1028736},
                    {"nombre": "Magangué", "poblacion": 144725},
                    {"nombre": "Turbaco", "poblacion": 94185},
                ],
            },
            {
                "codigo": "BOY",
                "nombre": "Boyacá",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Tunja", "es_capital": True, "poblacion": 203251},
                    {"nombre": "Duitama", "poblacion": 134312},
                    {"nombre": "Sogamoso", "poblacion": 121605},
                    {"nombre": "Chiquinquirá", "poblacion": 66272},
                ],
            },
            {
                "codigo": "CAL",
                "nombre": "Caldas",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Manizales", "es_capital": True, "poblacion": 434403},
                    {"nombre": "La Dorada", "poblacion": 82334},
                    {"nombre": "Chinchiná", "poblacion": 57849},
                ],
            },
            {
                "codigo": "CAQ",
                "nombre": "Caquetá",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Florencia", "es_capital": True, "poblacion": 185834},
                    {"nombre": "San Vicente del Caguán", "poblacion": 67612},
                ],
            },
            {
                "codigo": "CAS",
                "nombre": "Casanare",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Yopal", "es_capital": True, "poblacion": 148506},
                    {"nombre": "Aguazul", "poblacion": 40922},
                ],
            },
            {
                "codigo": "CAU",
                "nombre": "Cauca",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Popayán", "es_capital": True, "poblacion": 318059},
                    {"nombre": "Santander de Quilichao", "poblacion": 101827},
                ],
            },
            {
                "codigo": "CES",
                "nombre": "Cesar",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Valledupar", "es_capital": True, "poblacion": 490797},
                    {"nombre": "Aguachica", "poblacion": 99431},
                ],
            },
            {
                "codigo": "CHO",
                "nombre": "Chocó",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Quibdó", "es_capital": True, "poblacion": 129237},
                ],
            },
            {
                "codigo": "COR",
                "nombre": "Córdoba",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Montería", "es_capital": True, "poblacion": 502063},
                    {"nombre": "Sahagún", "poblacion": 97704},
                    {"nombre": "Lorica", "poblacion": 125000},
                ],
            },
            {
                "codigo": "CUN",
                "nombre": "Cundinamarca",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Soacha", "poblacion": 731020},
                    {"nombre": "Facatativá", "poblacion": 147454},
                    {"nombre": "Zipaquirá", "poblacion": 137505},
                    {"nombre": "Chía", "poblacion": 140948},
                    {"nombre": "Fusagasugá", "poblacion": 146559},
                    {"nombre": "Girardot", "poblacion": 107980},
                ],
            },
            {
                "codigo": "GUA",
                "nombre": "Guainía",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Inírida", "es_capital": True, "poblacion": 21497},
                ],
            },
            {
                "codigo": "GUV",
                "nombre": "Guaviare",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "San José del Guaviare", "es_capital": True, "poblacion": 58895},
                ],
            },
            {
                "codigo": "HUI",
                "nombre": "Huila",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Neiva", "es_capital": True, "poblacion": 362707},
                    {"nombre": "Pitalito", "poblacion": 134640},
                    {"nombre": "Garzón", "poblacion": 91908},
                ],
            },
            {
                "codigo": "LAG",
                "nombre": "La Guajira",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Riohacha", "es_capital": True, "poblacion": 279250},
                    {"nombre": "Maicao", "poblacion": 176824},
                ],
            },
            {
                "codigo": "MAG",
                "nombre": "Magdalena",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Santa Marta", "es_capital": True, "poblacion": 542113},
                    {"nombre": "Ciénaga", "poblacion": 107524},
                ],
            },
            {
                "codigo": "MET",
                "nombre": "Meta",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Villavicencio", "es_capital": True, "poblacion": 531275},
                    {"nombre": "Acacías", "poblacion": 76696},
                    {"nombre": "Granada", "poblacion": 70912},
                ],
            },
            {
                "codigo": "NAR",
                "nombre": "Nariño",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Pasto", "es_capital": True, "poblacion": 423217},
                    {"nombre": "Tumaco", "poblacion": 207826},
                    {"nombre": "Ipiales", "poblacion": 141141},
                ],
            },
            {
                "codigo": "NSA",
                "nombre": "Norte de Santander",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Cúcuta", "es_capital": True, "poblacion": 777106},
                    {"nombre": "Ocaña", "poblacion": 100526},
                    {"nombre": "Villa del Rosario", "poblacion": 102225},
                ],
            },
            {
                "codigo": "PUT",
                "nombre": "Putumayo",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Mocoa", "es_capital": True, "poblacion": 45762},
                ],
            },
            {
                "codigo": "QUI",
                "nombre": "Quindío",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Armenia", "es_capital": True, "poblacion": 307388},
                    {"nombre": "Calarcá", "poblacion": 79000},
                ],
            },
            {
                "codigo": "RIS",
                "nombre": "Risaralda",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Pereira", "es_capital": True, "poblacion": 488839},
                    {"nombre": "Dosquebradas", "poblacion": 204421},
                    {"nombre": "Santa Rosa de Cabal", "poblacion": 77501},
                ],
            },
            {
                "codigo": "SAP",
                "nombre": "San Andrés y Providencia",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "San Andrés", "es_capital": True, "poblacion": 75167},
                ],
            },
            {
                "codigo": "SAN",
                "nombre": "Santander",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Bucaramanga", "es_capital": True, "poblacion": 613400},
                    {"nombre": "Floridablanca", "poblacion": 275222},
                    {"nombre": "Barrancabermeja", "poblacion": 195711},
                    {"nombre": "Girón", "poblacion": 182162},
                ],
            },
            {
                "codigo": "SUC",
                "nombre": "Sucre",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Sincelejo", "es_capital": True, "poblacion": 289120},
                    {"nombre": "Corozal", "poblacion": 71908},
                ],
            },
            {
                "codigo": "TOL",
                "nombre": "Tolima",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Ibagué", "es_capital": True, "poblacion": 553524},
                    {"nombre": "Espinal", "poblacion": 81719},
                ],
            },
            {
                "codigo": "VAC",
                "nombre": "Valle del Cauca",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Cali", "es_capital": True, "poblacion": 2258244},
                    {"nombre": "Palmira", "poblacion": 318688},
                    {"nombre": "Buenaventura", "poblacion": 414808},
                    {"nombre": "Tuluá", "poblacion": 218147},
                    {"nombre": "Cartago", "poblacion": 137881},
                    {"nombre": "Buga", "poblacion": 129664},
                ],
            },
            {
                "codigo": "VAU",
                "nombre": "Vaupés",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Mitú", "es_capital": True, "poblacion": 17815},
                ],
            },
            {
                "codigo": "VID",
                "nombre": "Vichada",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Puerto Carreño", "es_capital": True, "poblacion": 16576},
                ],
            },
            {
                "codigo": "AMA",
                "nombre": "Amazonas",
                "timezone": "America/Bogota",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Leticia", "es_capital": True, "poblacion": 48144},
                ],
            },
        ]

        estados_creados = 0
        estados_actualizados = 0
        ciudades_creadas = 0
        ciudades_existentes = 0

        for depto_data in departamentos_colombia:
            # Crear o actualizar departamento
            estado, created = Estado.objects.update_or_create(
                pais="CO",
                codigo=depto_data["codigo"],
                defaults={
                    "nombre": depto_data["nombre"],
                    "sales_tax": depto_data["sales_tax"],
                    "timezone": depto_data["timezone"],
                },
            )

            if created:
                estados_creados += 1
                self.stdout.write(f"  ✅ Creado departamento: {estado.nombre} ({estado.codigo})")
            else:
                estados_actualizados += 1
                self.stdout.write(
                    f"  🔄 Actualizado departamento: {estado.nombre} ({estado.codigo})"
                )

            # Crear ciudades
            for ciudad_data in depto_data["ciudades"]:
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
                f"✅ Carga completada para Colombia:\n"
                f"   • Departamentos creados: {estados_creados}\n"
                f"   • Departamentos actualizados: {estados_actualizados}\n"
                f"   • Ciudades nuevas: {ciudades_creadas}\n"
                f"   • Ciudades existentes: {ciudades_existentes}\n"
                f"   • Total departamentos: {Estado.objects.filter(pais='CO').count()}\n"
                f"   • Total ciudades: {Ciudad.objects.filter(estado__pais='CO').count()}"
            )
        )
