"""
Comando para cargar departamentos y ciudades principales de Perú
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from taller.models.ubicacion import Ciudad, Estado


class Command(BaseCommand):
    help = "Carga los 25 departamentos de Perú y ciudades principales en la base de datos"

    def handle(self, *args, **options):
        self.stdout.write("[PE] Cargando departamentos de Peru...")

        # 25 departamentos de Perú con IGV (18%)
        departamentos_peru = [
            {"codigo": "LIM", "nombre": "Lima", "capital": "Lima", "igv": 18.00},
            {"codigo": "CAL", "nombre": "Callao", "capital": "Callao", "igv": 18.00},
            {"codigo": "ARE", "nombre": "Arequipa", "capital": "Arequipa", "igv": 18.00},
            {"codigo": "CUS", "nombre": "Cusco", "capital": "Cusco", "igv": 18.00},
            {"codigo": "LAL", "nombre": "La Libertad", "capital": "Trujillo", "igv": 18.00},
            {"codigo": "LAM", "nombre": "Lambayeque", "capital": "Chiclayo", "igv": 18.00},
            {"codigo": "PIU", "nombre": "Piura", "capital": "Piura", "igv": 18.00},
            {"codigo": "JUN", "nombre": "Junín", "capital": "Huancayo", "igv": 18.00},
            {"codigo": "PUN", "nombre": "Puno", "capital": "Puno", "igv": 18.00},
            {"codigo": "ICA", "nombre": "Ica", "capital": "Ica", "igv": 18.00},
            {"codigo": "ANC", "nombre": "Áncash", "capital": "Huaraz", "igv": 18.00},
            {"codigo": "HUA", "nombre": "Huánuco", "capital": "Huánuco", "igv": 18.00},
            {"codigo": "CAJ", "nombre": "Cajamarca", "capital": "Cajamarca", "igv": 18.00},
            {"codigo": "SMA", "nombre": "San Martín", "capital": "Moyobamba", "igv": 18.00},
            {"codigo": "LOR", "nombre": "Loreto", "capital": "Iquitos", "igv": 18.00},
            {"codigo": "AMA", "nombre": "Amazonas", "capital": "Chachapoyas", "igv": 18.00},
            {"codigo": "UCE", "nombre": "Ucayali", "capital": "Pucallpa", "igv": 18.00},
            {"codigo": "AYA", "nombre": "Ayacucho", "capital": "Ayacucho", "igv": 18.00},
            {"codigo": "APU", "nombre": "Apurímac", "capital": "Abancay", "igv": 18.00},
            {"codigo": "HUV", "nombre": "Huancavelica", "capital": "Huancavelica", "igv": 18.00},
            {"codigo": "PAS", "nombre": "Pasco", "capital": "Cerro de Pasco", "igv": 18.00},
            {"codigo": "TAC", "nombre": "Tacna", "capital": "Tacna", "igv": 18.00},
            {"codigo": "MOQ", "nombre": "Moquegua", "capital": "Moquegua", "igv": 18.00},
            {"codigo": "TUM", "nombre": "Tumbes", "capital": "Tumbes", "igv": 18.00},
            {
                "codigo": "MDD",
                "nombre": "Madre de Dios",
                "capital": "Puerto Maldonado",
                "igv": 18.00,
            },
        ]

        estados_creados = 0
        for depto_data in departamentos_peru:
            estado, created = Estado.objects.get_or_create(
                codigo=depto_data["codigo"],
                pais="PE",
                defaults={
                    "nombre": depto_data["nombre"],
                    "sales_tax": Decimal(str(depto_data["igv"])),
                    "timezone": "America/Lima",
                },
            )

            if created:
                estados_creados += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  [OK] {depto_data['nombre']} ({depto_data['codigo']})")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"  [EXISTE] {depto_data['nombre']} ({depto_data['codigo']}) ya existe"
                    )
                )

        self.stdout.write("")
        self.stdout.write(f"Departamentos creados: {estados_creados}/{len(departamentos_peru)}")

        # Ciudades principales de Perú
        self.stdout.write("")
        self.stdout.write("[CIUDADES] Cargando ciudades principales de Peru...")

        ciudades_peru = [
            # Lima
            {"nombre": "Lima", "estado": "LIM", "poblacion": 10000000, "es_capital": True},
            # Callao
            {"nombre": "Callao", "estado": "CAL", "poblacion": 1000000, "es_capital": True},
            # Arequipa
            {"nombre": "Arequipa", "estado": "ARE", "poblacion": 1100000, "es_capital": True},
            # Cusco
            {"nombre": "Cusco", "estado": "CUS", "poblacion": 450000, "es_capital": True},
            # La Libertad
            {"nombre": "Trujillo", "estado": "LAL", "poblacion": 1000000, "es_capital": True},
            # Lambayeque
            {"nombre": "Chiclayo", "estado": "LAM", "poblacion": 600000, "es_capital": True},
            # Piura
            {"nombre": "Piura", "estado": "PIU", "poblacion": 500000, "es_capital": True},
            # Junín
            {"nombre": "Huancayo", "estado": "JUN", "poblacion": 500000, "es_capital": True},
            # Puno
            {"nombre": "Puno", "estado": "PUN", "poblacion": 150000, "es_capital": True},
            # Ica
            {"nombre": "Ica", "estado": "ICA", "poblacion": 280000, "es_capital": True},
            # Áncash
            {"nombre": "Huaraz", "estado": "ANC", "poblacion": 130000, "es_capital": True},
            # Cajamarca
            {"nombre": "Cajamarca", "estado": "CAJ", "poblacion": 240000, "es_capital": True},
            # Loreto
            {"nombre": "Iquitos", "estado": "LOR", "poblacion": 440000, "es_capital": True},
            # Tacna
            {"nombre": "Tacna", "estado": "TAC", "poblacion": 310000, "es_capital": True},
            # San Martín
            {"nombre": "Tarapoto", "estado": "SMA", "poblacion": 190000, "es_capital": False},
            # Ucayali
            {"nombre": "Pucallpa", "estado": "UCE", "poblacion": 400000, "es_capital": True},
        ]

        ciudades_creadas = 0
        for ciudad_data in ciudades_peru:
            try:
                estado = Estado.objects.get(codigo=ciudad_data["estado"], pais="PE")
                ciudad, created = Ciudad.objects.get_or_create(
                    nombre=ciudad_data["nombre"],
                    estado=estado,
                    defaults={
                        "poblacion": ciudad_data["poblacion"],
                        "es_capital": ciudad_data["es_capital"],
                        "sales_tax_local": Decimal("0.00"),  # Sin impuesto local adicional
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
                        f"  [ERROR] Departamento {ciudad_data['estado']} no encontrado para {ciudad_data['nombre']}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(f"Ciudades creadas: {ciudades_creadas}/{len(ciudades_peru)}")
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("[PE] Departamentos y ciudades de Peru cargados exitosamente!")
        )
