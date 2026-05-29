"""
Comando para cargar las 16 regiones de Chile y sus principales ciudades
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from taller.models.ubicacion import Ciudad, Estado


class Command(BaseCommand):
    help = "Carga las 16 regiones de Chile y principales ciudades en la base de datos"

    def handle(self, *args, **options):
        self.stdout.write("[CL] Cargando regiones de Chile...")

        # 16 regiones de Chile con IVA 19%
        # Códigos ISO 3166-2:CL simplificados
        regiones_chile = [
            {
                "codigo": "AP",
                "nombre": "Arica y Parinacota",
                "timezone": "America/Santiago",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Arica", "es_capital": True, "poblacion": 221364},
                    {"nombre": "Putre", "poblacion": 2515},
                ],
            },
            {
                "codigo": "TA",
                "nombre": "Tarapacá",
                "timezone": "America/Santiago",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Iquique", "es_capital": True, "poblacion": 191468},
                    {"nombre": "Alto Hospicio", "poblacion": 108375},
                    {"nombre": "Pozo Almonte", "poblacion": 16960},
                ],
            },
            {
                "codigo": "AN",
                "nombre": "Antofagasta",
                "timezone": "America/Santiago",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Antofagasta", "es_capital": True, "poblacion": 425725},
                    {"nombre": "Calama", "poblacion": 165731},
                    {"nombre": "Tocopilla", "poblacion": 28079},
                    {"nombre": "Mejillones", "poblacion": 14776},
                ],
            },
            {
                "codigo": "AT",
                "nombre": "Atacama",
                "timezone": "America/Santiago",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Copiapó", "es_capital": True, "poblacion": 171766},
                    {"nombre": "Vallenar", "poblacion": 57003},
                    {"nombre": "Chañaral", "poblacion": 13000},
                ],
            },
            {
                "codigo": "CO",
                "nombre": "Coquimbo",
                "timezone": "America/Santiago",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "La Serena", "es_capital": True, "poblacion": 221054},
                    {"nombre": "Coquimbo", "poblacion": 227730},
                    {"nombre": "Ovalle", "poblacion": 123767},
                    {"nombre": "Illapel", "poblacion": 32948},
                ],
            },
            {
                "codigo": "VA",
                "nombre": "Valparaíso",
                "timezone": "America/Santiago",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Valparaíso", "es_capital": True, "poblacion": 296655},
                    {"nombre": "Viña del Mar", "poblacion": 334248},
                    {"nombre": "Quilpué", "poblacion": 151708},
                    {"nombre": "Villa Alemana", "poblacion": 126548},
                    {"nombre": "San Antonio", "poblacion": 96442},
                    {"nombre": "Quillota", "poblacion": 97572},
                    {"nombre": "Los Andes", "poblacion": 68093},
                    {"nombre": "San Felipe", "poblacion": 73711},
                ],
            },
            {
                "codigo": "RM",
                "nombre": "Región Metropolitana de Santiago",
                "timezone": "America/Santiago",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Santiago", "es_capital": True, "poblacion": 5220161},
                    {"nombre": "Puente Alto", "poblacion": 645909},
                    {"nombre": "Maipú", "poblacion": 578605},
                    {"nombre": "La Florida", "poblacion": 402433},
                    {"nombre": "San Bernardo", "poblacion": 334836},
                    {"nombre": "Las Condes", "poblacion": 330759},
                    {"nombre": "Pudahuel", "poblacion": 253139},
                    {"nombre": "Ñuñoa", "poblacion": 250192},
                    {"nombre": "Rancagua", "poblacion": 241774},
                    {"nombre": "Peñalolén", "poblacion": 266798},
                    {"nombre": "El Bosque", "poblacion": 162505},
                    {"nombre": "La Pintana", "poblacion": 189335},
                    {"nombre": "San Miguel", "poblacion": 133059},
                    {"nombre": "Quilicura", "poblacion": 254694},
                    {"nombre": "Recoleta", "poblacion": 190075},
                    {"nombre": "Colina", "poblacion": 180353},
                    {"nombre": "Melipilla", "poblacion": 141165},
                ],
            },
            {
                "codigo": "LI",
                "nombre": "Libertador General Bernardo O'Higgins",
                "timezone": "America/Santiago",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "San Fernando", "poblacion": 73973},
                    {"nombre": "Rengo", "poblacion": 62161},
                    {"nombre": "Pichilemu", "poblacion": 16456},
                ],
            },
            {
                "codigo": "ML",
                "nombre": "Maule",
                "timezone": "America/Santiago",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Talca", "es_capital": True, "poblacion": 236724},
                    {"nombre": "Curicó", "poblacion": 163096},
                    {"nombre": "Linares", "poblacion": 99540},
                    {"nombre": "Cauquenes", "poblacion": 44143},
                    {"nombre": "Constitución", "poblacion": 50348},
                ],
            },
            {
                "codigo": "NB",
                "nombre": "Ñuble",
                "timezone": "America/Santiago",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Chillán", "es_capital": True, "poblacion": 198624},
                    {"nombre": "San Carlos", "poblacion": 56252},
                    {"nombre": "Bulnes", "poblacion": 22607},
                ],
            },
            {
                "codigo": "BI",
                "nombre": "Biobío",
                "timezone": "America/Santiago",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Concepción", "es_capital": True, "poblacion": 238092},
                    {"nombre": "Talcahuano", "poblacion": 151749},
                    {"nombre": "Los Ángeles", "poblacion": 218515},
                    {"nombre": "Chiguayante", "poblacion": 88277},
                    {"nombre": "Coronel", "poblacion": 116262},
                    {"nombre": "San Pedro de la Paz", "poblacion": 145906},
                    {"nombre": "Penco", "poblacion": 51984},
                    {"nombre": "Tomé", "poblacion": 58729},
                ],
            },
            {
                "codigo": "AR",
                "nombre": "La Araucanía",
                "timezone": "America/Santiago",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Temuco", "es_capital": True, "poblacion": 302931},
                    {"nombre": "Angol", "poblacion": 56058},
                    {"nombre": "Villarrica", "poblacion": 59103},
                    {"nombre": "Pucón", "poblacion": 29782},
                ],
            },
            {
                "codigo": "LR",
                "nombre": "Los Ríos",
                "timezone": "America/Santiago",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Valdivia", "es_capital": True, "poblacion": 176774},
                    {"nombre": "La Unión", "poblacion": 39447},
                    {"nombre": "Río Bueno", "poblacion": 32766},
                ],
            },
            {
                "codigo": "LL",
                "nombre": "Los Lagos",
                "timezone": "America/Santiago",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Puerto Montt", "es_capital": True, "poblacion": 269398},
                    {"nombre": "Osorno", "poblacion": 173410},
                    {"nombre": "Castro", "poblacion": 47607},
                    {"nombre": "Ancud", "poblacion": 42458},
                    {"nombre": "Puerto Varas", "poblacion": 48620},
                ],
            },
            {
                "codigo": "AI",
                "nombre": "Aysén del General Carlos Ibáñez del Campo",
                "timezone": "America/Santiago",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Coyhaique", "es_capital": True, "poblacion": 61210},
                    {"nombre": "Puerto Aysén", "poblacion": 24294},
                    {"nombre": "Chile Chico", "poblacion": 5121},
                ],
            },
            {
                "codigo": "MA",
                "nombre": "Magallanes y de la Antártica Chilena",
                "timezone": "America/Punta_Arenas",
                "sales_tax": Decimal("19.00"),
                "ciudades": [
                    {"nombre": "Punta Arenas", "es_capital": True, "poblacion": 141984},
                    {"nombre": "Puerto Natales", "poblacion": 23782},
                    {"nombre": "Porvenir", "poblacion": 7323},
                ],
            },
        ]

        estados_creados = 0
        estados_actualizados = 0
        ciudades_creadas = 0
        ciudades_existentes = 0

        for region_data in regiones_chile:
            # Crear o actualizar región
            estado, created = Estado.objects.update_or_create(
                pais="CL",
                codigo=region_data["codigo"],
                defaults={
                    "nombre": region_data["nombre"],
                    "sales_tax": region_data["sales_tax"],
                    "timezone": region_data["timezone"],
                },
            )

            if created:
                estados_creados += 1
                self.stdout.write(f"  ✅ Creada región: {estado.nombre} ({estado.codigo})")
            else:
                estados_actualizados += 1
                self.stdout.write(f"  🔄 Actualizada región: {estado.nombre} ({estado.codigo})")

            # Crear ciudades
            for ciudad_data in region_data["ciudades"]:
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
                f"✅ Carga completada para Chile:\n"
                f"   • Regiones creadas: {estados_creados}\n"
                f"   • Regiones actualizadas: {estados_actualizados}\n"
                f"   • Ciudades nuevas: {ciudades_creadas}\n"
                f"   • Ciudades existentes: {ciudades_existentes}\n"
                f"   • Total regiones: {Estado.objects.filter(pais='CL').count()}\n"
                f"   • Total ciudades: {Ciudad.objects.filter(estado__pais='CL').count()}"
            )
        )
