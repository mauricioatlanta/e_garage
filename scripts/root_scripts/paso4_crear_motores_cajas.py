#!/usr/bin/env python
"""
🎯 PASO 4: CREAR DATOS DEMO PARA MOTORES Y CAJAS
Crear motores y cajas para los modelos de vehículos existentes
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.extras_vehiculo import CajaVehiculo, MotorVehiculo
from taller.models.modelo import Modelo


def crear_motores_cajas_demo():
    """Crear motores y cajas para modelos existentes"""
    print("🔧 CREANDO MOTORES Y CAJAS DEMO")
    print("🎯 Dependencia jerárquica Marca → Modelo → Motor/Caja")
    print("=" * 60)

    # Definir motores por tipo de vehículo
    motores_datos = {
        # Motores para autos compactos/sedán
        "compactos": ["1.6L 4 Cil", "1.8L 4 Cil", "2.0L 4 Cil"],
        # Motores para SUVs/Trucks
        "grandes": ["2.4L 4 Cil", "3.0L V6", "3.5L V6", "5.0L V8"],
        # Motores híbridos
        "hibridos": ["1.8L Hybrid", "2.0L Hybrid", "2.5L Hybrid"],
    }

    # Definir cajas por tipo
    cajas_datos = {
        "manual": ["Manual 5 vel", "Manual 6 vel"],
        "automatica": [
            "Automática 4 vel",
            "Automática 6 vel",
            "CVT",
            "Automática 8 vel",
        ],
        "hibrida": ["E-CVT", "Hybrid CVT"],
    }

    # Mapear modelos a tipos de motor y caja
    mapeo_modelos = {
        # Toyota
        "Corolla": ("compactos", ["manual", "automatica"]),
        "Camry": ("compactos", ["automatica"]),
        "RAV4": ("grandes", ["automatica"]),
        "Prius": ("hibridos", ["hibrida"]),
        # Ford
        "Fiesta": ("compactos", ["manual", "automatica"]),
        "Focus": ("compactos", ["manual", "automatica"]),
        "F-150": ("grandes", ["manual", "automatica"]),
        "Explorer": ("grandes", ["automatica"]),
        # Chevrolet
        "Spark": ("compactos", ["manual", "automatica"]),
        "Cruze": ("compactos", ["manual", "automatica"]),
        "Silverado": ("grandes", ["manual", "automatica"]),
        "Equinox": ("grandes", ["automatica"]),
        # Hyundai
        "Accent": ("compactos", ["manual", "automatica"]),
        "Elantra": ("compactos", ["manual", "automatica"]),
        "Tucson": ("grandes", ["automatica"]),
        "Santa Fe": ("grandes", ["automatica"]),
        # Honda
        "Civic": ("compactos", ["manual", "automatica"]),
        "Accord": ("compactos", ["automatica"]),
        "CR-V": ("grandes", ["automatica"]),
        "Pilot": ("grandes", ["automatica"]),
        # Nissan
        "Sentra": ("compactos", ["manual", "automatica"]),
        "Altima": ("compactos", ["automatica"]),
        "Rogue": ("grandes", ["automatica"]),
        "Pathfinder": ("grandes", ["automatica"]),
    }

    motores_creados = 0
    cajas_creadas = 0

    # Procesar todos los modelos existentes
    modelos = Modelo.objects.all()

    for modelo in modelos:
        print(f"\n🚗 {modelo.marca.nombre} {modelo.nombre} ({modelo.country})")

        # Determinar tipo de motor y cajas basado en el mapeo
        if modelo.nombre in mapeo_modelos:
            tipo_motor, tipos_caja = mapeo_modelos[modelo.nombre]
        else:
            # NO crear motores/cajas para modelos no mapeados
            print("   ⚠️  Modelo no mapeado - saltando creación de motores/cajas")
            continue

        # Crear motores para este modelo
        motores_modelo = motores_datos[tipo_motor]
        for motor_nombre in motores_modelo:
            motor, created = MotorVehiculo.objects.get_or_create(nombre=motor_nombre)
            if created:
                motores_creados += 1
                print(f"   ⚙️ Motor: {motor_nombre}")

            # Agregar el modelo a la relación ManyToMany si no está ya asociado
            if modelo not in motor.modelos.all():
                motor.modelos.add(modelo)

        # Crear cajas para este modelo
        for tipo_caja in tipos_caja:
            cajas_tipo = cajas_datos[tipo_caja]
            for caja_nombre in cajas_tipo:
                caja, created = CajaVehiculo.objects.get_or_create(nombre=caja_nombre)
                if created:
                    cajas_creadas += 1
                    print(f"   🔧 Caja: {caja_nombre}")

                # Agregar el modelo a la relación ManyToMany si no está ya asociado
                if modelo not in caja.modelos.all():
                    caja.modelos.add(modelo)

    print("\n📊 RESUMEN:")
    print(f"   ⚙️ Motores creados: {motores_creados}")
    print(f"   🔧 Cajas creadas: {cajas_creadas}")
    print(f"   🚗 Modelos procesados: {modelos.count()}")

    # Verificar datos por país
    motores_cl = MotorVehiculo.objects.filter(country="CL").count()
    motores_us = MotorVehiculo.objects.filter(country="US").count()
    cajas_cl = CajaVehiculo.objects.filter(country="CL").count()
    cajas_us = CajaVehiculo.objects.filter(country="US").count()

    print("\n🌍 POR PAÍS:")
    print(f"   🇨🇱 Chile: {motores_cl} motores, {cajas_cl} cajas")
    print(f"   🇺🇸 USA: {motores_us} motores, {cajas_us} cajas")

    print("\n✅ DATOS DEMO CREADOS EXITOSAMENTE")
    print("🎯 Sistema listo para dependencia jerárquica")


if __name__ == "__main__":
    crear_motores_cajas_demo()
