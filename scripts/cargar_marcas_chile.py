#!/usr/bin/env python
"""
Script para cargar marcas comunes de vehículos en Chile
"""
import os

import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.marca import Marca


def main():
    print("🚗 Cargando marcas de vehículos para Chile\n")
    
    # Marcas comunes en Chile
    marcas_chile = [
        'Toyota', 'Chevrolet', 'Ford', 'Nissan', 'Hyundai', 'Kia',
        'Mazda', 'Suzuki', 'Mitsubishi', 'Honda', 'Volkswagen', 'Renault',
        'Peugeot', 'Citroën', 'Fiat', 'Subaru', 'Isuzu', 'Great Wall',
        'Chery', 'JAC', 'BYD', 'Geely', 'BMW', 'Mercedes-Benz', 'Audi',
        'Volvo', 'Land Rover', 'Jeep', 'Dodge', 'Chrysler'
    ]
    
    creadas = 0
    existentes = 0
    
    for marca_nombre in marcas_chile:
        marca, created = Marca.objects.get_or_create(
            nombre=marca_nombre,
            country='CL',
            defaults={'nombre': marca_nombre, 'country': 'CL'}
        )
        
        if created:
            print(f"✅ Marca creada: {marca_nombre}")
            creadas += 1
        else:
            print(f"📍 Marca ya existe: {marca_nombre}")
            existentes += 1
    
    print(f"\n🎉 RESUMEN:")
    print(f"✅ Marcas creadas: {creadas}")
    print(f"📍 Marcas ya existentes: {existentes}")
    print(f"🚗 Total marcas Chile: {Marca.objects.filter(country='CL').count()}")

if __name__ == '__main__':
    main()
