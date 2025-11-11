"""
Comando para cargar estados y ciudades principales de Venezuela
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from taller.models.ubicacion import Ciudad, Estado


class Command(BaseCommand):
    help = "Carga los 24 estados de Venezuela y ciudades principales en la base de datos"

    def handle(self, *args, **options):
        self.stdout.write("[VE] Cargando estados de Venezuela...")

        # 23 estados + Distrito Capital de Venezuela con IVA (16%)
        estados_venezuela = [
            {"codigo": "DC", "nombre": "Distrito Capital", "capital": "Caracas", "iva": 16.00},
            {"codigo": "AM", "nombre": "Amazonas", "capital": "Puerto Ayacucho", "iva": 16.00},
            {"codigo": "AN", "nombre": "Anzoátegui", "capital": "Barcelona", "iva": 16.00},
            {"codigo": "AP", "nombre": "Apure", "capital": "San Fernando de Apure", "iva": 16.00},
            {"codigo": "AR", "nombre": "Aragua", "capital": "Maracay", "iva": 16.00},
            {"codigo": "BA", "nombre": "Barinas", "capital": "Barinas", "iva": 16.00},
            {"codigo": "BO", "nombre": "Bolívar", "capital": "Ciudad Bolívar", "iva": 16.00},
            {"codigo": "CA", "nombre": "Carabobo", "capital": "Valencia", "iva": 16.00},
            {"codigo": "CO", "nombre": "Cojedes", "capital": "San Carlos", "iva": 16.00},
            {"codigo": "DA", "nombre": "Delta Amacuro", "capital": "Tucupita", "iva": 16.00},
            {"codigo": "FA", "nombre": "Falcón", "capital": "Coro", "iva": 16.00},
            {
                "codigo": "GU",
                "nombre": "Guárico",
                "capital": "San Juan de los Morros",
                "iva": 16.00,
            },
            {"codigo": "LA", "nombre": "Lara", "capital": "Barquisimeto", "iva": 16.00},
            {"codigo": "ME", "nombre": "Mérida", "capital": "Mérida", "iva": 16.00},
            {"codigo": "MI", "nombre": "Miranda", "capital": "Los Teques", "iva": 16.00},
            {"codigo": "MO", "nombre": "Monagas", "capital": "Maturín", "iva": 16.00},
            {"codigo": "NE", "nombre": "Nueva Esparta", "capital": "La Asunción", "iva": 16.00},
            {"codigo": "PO", "nombre": "Portuguesa", "capital": "Guanare", "iva": 16.00},
            {"codigo": "SU", "nombre": "Sucre", "capital": "Cumaná", "iva": 16.00},
            {"codigo": "TA", "nombre": "Táchira", "capital": "San Cristóbal", "iva": 16.00},
            {"codigo": "TR", "nombre": "Trujillo", "capital": "Trujillo", "iva": 16.00},
            {"codigo": "VA", "nombre": "Vargas", "capital": "La Guaira", "iva": 16.00},
            {"codigo": "YA", "nombre": "Yaracuy", "capital": "San Felipe", "iva": 16.00},
            {"codigo": "ZU", "nombre": "Zulia", "capital": "Maracaibo", "iva": 16.00},
        ]

        estados_creados = 0
        for estado_data in estados_venezuela:
            estado, created = Estado.objects.get_or_create(
                codigo=estado_data["codigo"],
                pais="VE",
                defaults={
                    "nombre": estado_data["nombre"],
                    "sales_tax": Decimal(str(estado_data["iva"])),
                    "timezone": "America/Caracas",
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
        self.stdout.write(f"Estados creados: {estados_creados}/{len(estados_venezuela)}")

        # Ciudades principales de Venezuela
        self.stdout.write("")
        self.stdout.write("[CIUDADES] Cargando ciudades principales de Venezuela...")

        ciudades_venezuela = [
            # Distrito Capital
            {"nombre": "Caracas", "estado": "DC", "poblacion": 2100000, "es_capital": True},
            # Zulia
            {"nombre": "Maracaibo", "estado": "ZU", "poblacion": 1900000, "es_capital": True},
            # Carabobo
            {"nombre": "Valencia", "estado": "CA", "poblacion": 1400000, "es_capital": True},
            # Anzoátegui
            {"nombre": "Barcelona", "estado": "AN", "poblacion": 350000, "es_capital": True},
            {"nombre": "Puerto La Cruz", "estado": "AN", "poblacion": 380000, "es_capital": False},
            # Aragua
            {"nombre": "Maracay", "estado": "AR", "poblacion": 1200000, "es_capital": True},
            # Lara
            {"nombre": "Barquisimeto", "estado": "LA", "poblacion": 1200000, "es_capital": True},
            # Táchira
            {"nombre": "San Cristóbal", "estado": "TA", "poblacion": 410000, "es_capital": True},
            # Miranda
            {"nombre": "Los Teques", "estado": "MI", "poblacion": 240000, "es_capital": True},
            # Bolívar
            {"nombre": "Ciudad Bolívar", "estado": "BO", "poblacion": 370000, "es_capital": True},
            {"nombre": "Puerto Ordaz", "estado": "BO", "poblacion": 750000, "es_capital": False},
            # Monagas
            {"nombre": "Maturín", "estado": "MO", "poblacion": 500000, "es_capital": True},
            # Mérida
            {"nombre": "Mérida", "estado": "ME", "poblacion": 300000, "es_capital": True},
            # Sucre
            {"nombre": "Cumaná", "estado": "SU", "poblacion": 400000, "es_capital": True},
            # Nueva Esparta
            {"nombre": "La Asunción", "estado": "NE", "poblacion": 30000, "es_capital": True},
            {"nombre": "Porlamar", "estado": "NE", "poblacion": 120000, "es_capital": False},
            # Falcón
            {"nombre": "Coro", "estado": "FA", "poblacion": 230000, "es_capital": True},
            # Vargas
            {"nombre": "La Guaira", "estado": "VA", "poblacion": 150000, "es_capital": True},
            # Barinas
            {"nombre": "Barinas", "estado": "BA", "poblacion": 350000, "es_capital": True},
            # Guárico
            {
                "nombre": "San Juan de los Morros",
                "estado": "GU",
                "poblacion": 130000,
                "es_capital": True,
            },
        ]

        ciudades_creadas = 0
        for ciudad_data in ciudades_venezuela:
            try:
                estado = Estado.objects.get(codigo=ciudad_data["estado"], pais="VE")
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
                        f"  [ERROR] Estado {ciudad_data['estado']} no encontrado para {ciudad_data['nombre']}"
                    )
                )

        self.stdout.write("")
        self.stdout.write(f"Ciudades creadas: {ciudades_creadas}/{len(ciudades_venezuela)}")
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("[VE] Estados y ciudades de Venezuela cargados exitosamente!")
        )
