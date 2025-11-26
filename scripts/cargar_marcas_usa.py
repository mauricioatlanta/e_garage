#!/usr/bin/env python
"""
Script para cargar marcas comunes de vehículos en USA
"""

import os
import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.marca import Marca


def main():
    print("🚗 Cargando marcas de vehículos para USA\n")

    # Marcas comunes en USA
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
            print(f"✅ Marca creada: {marca_nombre}")
            creadas += 1
        else:
            print(f"📍 Marca ya existe: {marca_nombre}")
            existentes += 1

    print("\n🎉 RESUMEN:")
    print(f"✅ Marcas creadas: {creadas}")
    print(f"📍 Marcas ya existentes: {existentes}")
    print(f"🚗 Total marcas USA: {Marca.objects.filter(country='US').count()}")


if __name__ == "__main__":
    main()
