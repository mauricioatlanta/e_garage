"""
Comando de gestión para cargar modelos de vehículos para USA
Ejecutar: python manage.py cargar_modelos_usa
"""

from django.core.management.base import BaseCommand
from django.db import models

from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.vehiculos.usa_model_catalog import USA_MODELS_BY_MAKE


class Command(BaseCommand):
    help = "Carga modelos comunes de vehículos para USA por marca"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚗 Cargando modelos de vehículos para USA\n"))

        total_creados = 0
        total_existentes = 0
        marcas_sin_encontrar = []

        for marca_nombre, modelos_lista in USA_MODELS_BY_MAKE.items():
            # Buscar la marca
            try:
                marca = Marca.objects.get(nombre=marca_nombre, country="US")
                self.stdout.write(f"\n📦 {marca_nombre}:")
            except Marca.DoesNotExist:
                marcas_sin_encontrar.append(marca_nombre)
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Marca '{marca_nombre}' no encontrada (country='US')")
                )
                continue

            # Crear modelos para esta marca
            for modelo_nombre in modelos_lista:
                modelo, created = Modelo.objects.get_or_create(
                    nombre=modelo_nombre,
                    marca=marca,
                    country="US",
                    defaults={"nombre": modelo_nombre, "marca": marca, "country": "US"},
                )

                if created:
                    self.stdout.write(f"  ✅ Creado: {modelo_nombre}")
                    total_creados += 1
                else:
                    self.stdout.write(f"  📍 Ya existe: {modelo_nombre}")
                    total_existentes += 1

        # Resumen
        self.stdout.write(self.style.SUCCESS("\n🎉 RESUMEN:"))
        self.stdout.write(self.style.SUCCESS(f"✅ Modelos creados: {total_creados}"))
        self.stdout.write(f"📍 Modelos ya existentes: {total_existentes}")
        self.stdout.write(
            self.style.SUCCESS(
                f"🚗 Total modelos USA: {Modelo.objects.filter(country='US').count()}"
            )
        )

        if marcas_sin_encontrar:
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️  Marcas no encontradas ({len(marcas_sin_encontrar)}): {', '.join(marcas_sin_encontrar)}"
                )
            )
            self.stdout.write("   💡 Ejecuta primero: python manage.py cargar_marcas_usa")

        # Estadísticas por marca
        self.stdout.write("\n📊 Estadísticas por marca:")
        marcas_con_modelos = (
            Modelo.objects.filter(country="US")
            .values("marca__nombre")
            .annotate(total=models.Count("id"))
            .order_by("-total")[:10]
        )
        for item in marcas_con_modelos:
            self.stdout.write(f"  {item['marca__nombre']}: {item['total']} modelos")
