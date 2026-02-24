"""
Comando de gestión para cargar marcas de vehículos para USA
Ejecutar: python manage.py cargar_marcas_usa
"""

from django.core.management.base import BaseCommand

from taller.models.marca import Marca


class Command(BaseCommand):
    help = "Carga marcas comunes de vehículos para USA"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚗 Cargando marcas de vehículos para USA\n"))

        # Marcas comunes en USA (40 marcas)
        marcas_usa = [
            "Acura",
            "Audi",
            "BMW",
            "Buick",
            "Cadillac",
            "Chevrolet",
            "Chrysler",
            "Dodge",
            "Ford",
            "GMC",
            "Honda",
            "Hyundai",
            "Infiniti",
            "Jeep",
            "Kia",
            "Lexus",
            "Lincoln",
            "Mazda",
            "Mercedes-Benz",
            "Mitsubishi",
            "Nissan",
            "Ram",
            "Subaru",
            "Toyota",
            "Volkswagen",
            "Volvo",
            "Tesla",
            "Genesis",
            "Alfa Romeo",
            "Jaguar",
            "Land Rover",
            "Porsche",
            "Mini",
            "Fiat",
            "Maserati",
            "Bentley",
            "Rolls-Royce",
            "Aston Martin",
            "McLaren",
            "Ferrari",
            "Lamborghini",
        ]

        creadas = 0
        existentes = 0

        for marca_nombre in marcas_usa:
            marca, created = Marca.objects.get_or_create(
                nombre=marca_nombre,
                country="US",
                defaults={"nombre": marca_nombre, "country": "US"},
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Marca creada: {marca_nombre}"))
                creadas += 1
            else:
                self.stdout.write(f"📍 Marca ya existe: {marca_nombre}")
                existentes += 1

        total = Marca.objects.filter(country="US").count()
        self.stdout.write(self.style.SUCCESS("\n🎉 RESUMEN:"))
        self.stdout.write(self.style.SUCCESS(f"✅ Marcas creadas: {creadas}"))
        self.stdout.write(f"📍 Marcas ya existentes: {existentes}")
        self.stdout.write(self.style.SUCCESS(f"🚗 Total marcas USA: {total}"))

        if total == 0:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  ADVERTENCIA: No se encontraron marcas para USA después de la carga."
                )
            )
            self.stdout.write(
                "   Verifica que el modelo Marca tenga el campo 'country' configurado correctamente."
            )
