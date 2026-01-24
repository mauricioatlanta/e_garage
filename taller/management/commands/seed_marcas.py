"""
Management command para seedear marcas globales y regionales con deduplicación inteligente.

Este comando:
1. Define marcas globales (country='gl') que están disponibles en todos los países
2. Define marcas regionales específicas por país
3. Detecta y unifica duplicados (ej: "Toyota" en CL y MX → se convierte en "Toyota GL")
4. Actualiza todos los Vehiculos existentes para que apunten a la marca global
5. Elimina los registros duplicados

Uso:
    python manage.py seed_marcas
    python manage.py seed_marcas --dry-run  # Solo muestra lo que haría sin hacer cambios
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from taller.models.marca import Marca
from taller.models.vehiculos import Vehiculo


# Marcas Globales: Disponibles en todos los países
MARCAS_GLOBALES = [
    "Toyota",
    "Hyundai",
    "Kia",
    "Nissan",
    "Honda",
    "Mazda",
    "Ford",
    "Chevrolet",
    "Volkswagen",
    "BMW",
    "Mercedes-Benz",
    "Audi",
    "Volvo",
    "Subaru",
    "Mitsubishi",
    "Suzuki",
    "Peugeot",
    "Renault",
    "Citroën",
    "Fiat",
    "Jeep",
    "Dodge",
    "Ram",
    "GMC",
    "Cadillac",
    "Lincoln",
    "Lexus",
    "Infiniti",
    "Acura",
    "Porsche",
    "Jaguar",
    "Land Rover",
    "Mini",
    "Smart",
    "Tesla",
]

# Marcas Regionales: Específicas de cada país
MARCAS_REGIONALES = {
    "CL": [
        "Chery",
        "Great Wall",
        "Geely",
        "BYD",
        "JAC",
        "DFSK",
        "Foton",
        "Dongfeng",
    ],
    "US": [
        "Buick",
        "Chrysler",
        "Genesis",
        "Rivian",
        "Lucid",
    ],
    "MX": [
        "Dina",
        "Mastretta",
        "Vuhl",
    ],
}


class Command(BaseCommand):
    help = "Seed de marcas globales y regionales con deduplicación inteligente"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Muestra lo que haría sin hacer cambios reales",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Fuerza la creación incluso si ya existen marcas",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        force = options["force"]

        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🚀 SEED DE MARCAS GLOBALES Y REGIONALES"))
        self.stdout.write("=" * 80)

        if dry_run:
            self.stdout.write(self.style.WARNING("\n⚠️  MODO DRY-RUN: No se harán cambios reales\n"))

        with transaction.atomic():
            # Paso 1: Crear marcas globales
            self.stdout.write("\n1️⃣ Creando marcas globales (country='gl')...")
            marcas_globales_creadas = self._crear_marcas_globales(dry_run, force)

            # Paso 2: Crear marcas regionales
            self.stdout.write("\n2️⃣ Creando marcas regionales...")
            marcas_regionales_creadas = self._crear_marcas_regionales(dry_run, force)

            # Paso 3: Detectar y unificar duplicados
            self.stdout.write("\n3️⃣ Detectando y unificando duplicados...")
            duplicados_unificados = self._unificar_duplicados(dry_run)

            # Resumen
            self.stdout.write("\n" + "=" * 80)
            self.stdout.write(self.style.SUCCESS("✅ PROCESO COMPLETADO"))
            self.stdout.write("=" * 80)
            self.stdout.write(f"\n📊 RESUMEN:")
            self.stdout.write(f"   • Marcas globales creadas: {marcas_globales_creadas}")
            self.stdout.write(f"   • Marcas regionales creadas: {marcas_regionales_creadas}")
            self.stdout.write(f"   • Duplicados unificados: {duplicados_unificados}")

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        "\n⚠️  Este fue un DRY-RUN. Ejecuta sin --dry-run para aplicar los cambios."
                    )
                )

    def _crear_marcas_globales(self, dry_run, force):
        """Crea marcas globales (country='gl')"""
        creadas = 0
        for nombre_marca in MARCAS_GLOBALES:
            nombre_normalizado = nombre_marca.strip()

            # Verificar si ya existe como global
            existe_global = Marca.objects.filter(
                country="gl", nombre__iexact=nombre_normalizado
            ).exists()

            if existe_global and not force:
                self.stdout.write(
                    f"   ⏭️  '{nombre_normalizado}' ya existe como global, omitiendo..."
                )
                continue

            if not dry_run:
                marca, created = Marca.objects.get_or_create(
                    country="gl",
                    nombre=nombre_normalizado,
                    defaults={"nombre": nombre_normalizado, "country": "gl"},
                )
                if created:
                    creadas += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"   ✅ Creada marca global: {nombre_normalizado}")
                    )
                else:
                    self.stdout.write(
                        f"   ℹ️  Marca global '{nombre_normalizado}' ya existía"
                    )
            else:
                if not existe_global:
                    creadas += 1
                    self.stdout.write(
                        f"   [DRY-RUN] Crearía marca global: {nombre_normalizado}"
                    )

        return creadas

    def _crear_marcas_regionales(self, dry_run, force):
        """Crea marcas regionales por país"""
        total_creadas = 0
        for country, marcas in MARCAS_REGIONALES.items():
            self.stdout.write(f"\n   📍 País: {country}")
            creadas_pais = 0
            for nombre_marca in marcas:
                nombre_normalizado = nombre_marca.strip()

                # Verificar si ya existe como regional
                existe_regional = Marca.objects.filter(
                    country=country, nombre__iexact=nombre_normalizado
                ).exists()

                # Verificar si existe como global (no crear duplicado)
                existe_global = Marca.objects.filter(
                    country="gl", nombre__iexact=nombre_normalizado
                ).exists()

                if existe_global:
                    self.stdout.write(
                        f"   ⏭️  '{nombre_normalizado}' ya existe como global, omitiendo regional..."
                    )
                    continue

                if existe_regional and not force:
                    self.stdout.write(
                        f"   ⏭️  '{nombre_normalizado}' ya existe en {country}, omitiendo..."
                    )
                    continue

                if not dry_run:
                    marca, created = Marca.objects.get_or_create(
                        country=country,
                        nombre=nombre_normalizado,
                        defaults={"nombre": nombre_normalizado, "country": country},
                    )
                    if created:
                        creadas_pais += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"      ✅ Creada marca regional: {nombre_normalizado} ({country})"
                            )
                        )
                else:
                    if not existe_regional:
                        creadas_pais += 1
                        self.stdout.write(
                            f"      [DRY-RUN] Crearía marca regional: {nombre_normalizado} ({country})"
                        )

            total_creadas += creadas_pais
            self.stdout.write(f"   📊 Total creadas en {country}: {creadas_pais}")

        return total_creadas

    def _unificar_duplicados(self, dry_run):
        """Detecta duplicados y los unifica en marcas globales"""
        unificados = 0

        # Buscar marcas que existen en múltiples países (potenciales duplicados)
        self.stdout.write("\n   🔍 Buscando duplicados...")

        # Obtener todas las marcas que no son globales
        marcas_regionales = Marca.objects.exclude(country="gl").order_by("nombre")

        # Agrupar por nombre normalizado (case-insensitive)
        marcas_por_nombre = {}
        for marca in marcas_regionales:
            nombre_normalizado = marca.nombre.strip().lower()
            if nombre_normalizado not in marcas_por_nombre:
                marcas_por_nombre[nombre_normalizado] = []
            marcas_por_nombre[nombre_normalizado].append(marca)

        # Procesar duplicados
        for nombre_normalizado, marcas_duplicadas in marcas_por_nombre.items():
            if len(marcas_duplicadas) <= 1:
                continue  # No es duplicado

            # Verificar si ya existe una marca global con este nombre
            nombre_original = marcas_duplicadas[0].nombre.strip()
            marca_global = Marca.objects.filter(
                country="gl", nombre__iexact=nombre_original
            ).first()

            if not marca_global:
                # Crear marca global si no existe
                self.stdout.write(
                    f"\n   🔄 Unificando '{nombre_original}' en marca global..."
                )
                if not dry_run:
                    marca_global, created = Marca.objects.get_or_create(
                        country="gl",
                        nombre=nombre_original,
                        defaults={"nombre": nombre_original, "country": "gl"},
                    )
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"      ✅ Creada marca global: {nombre_original}"
                            )
                        )
                else:
                    marca_global = type("obj", (object,), {"id": None, "nombre": nombre_original})()
                    self.stdout.write(
                        f"      [DRY-RUN] Crearía marca global: {nombre_original}"
                    )

            # Actualizar todos los vehículos que usan las marcas regionales
            for marca_regional in marcas_duplicadas:
                vehiculos_afectados = Vehiculo.objects.filter(marca=marca_regional).count()

                if vehiculos_afectados > 0:
                    self.stdout.write(
                        f"      📦 Actualizando {vehiculos_afectados} vehículo(s) de '{marca_regional.nombre}' ({marca_regional.country}) → '{marca_global.nombre}' (gl)"
                    )

                    if not dry_run:
                        Vehiculo.objects.filter(marca=marca_regional).update(
                            marca=marca_global
                        )

                # Eliminar marca regional duplicada
                self.stdout.write(
                    f"      🗑️  Eliminando marca duplicada: {marca_regional.nombre} ({marca_regional.country})"
                )
                if not dry_run:
                    marca_regional.delete()

                unificados += 1

        return unificados

