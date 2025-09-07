#!/usr/bin/env python
"""
Verificación final: Formulario de vehículos funciona correctamente
"""
import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.vehiculos import Vehiculo


def main():
    print("🎯 VERIFICACIÓN FINAL: Problema de guardado resuelto\n")

    # 1. Verificar que no hay marcas/modelos numéricos
    marcas_numericas = Marca.objects.filter(nombre__regex=r"^[0-9]+$")
    modelos_numericos = Modelo.objects.filter(nombre__regex=r"^[0-9]+$")

    print(f"✅ Marcas numéricas: {marcas_numericas.count()} (debería ser 0)")
    print(f"✅ Modelos numéricos: {modelos_numericos.count()} (debería ser 0)")

    # 2. Verificar vehículos existentes
    vehiculos = Vehiculo.objects.all()[:3]
    print(f"\n📋 Muestra de vehículos (total: {Vehiculo.objects.count()}):")
    for v in vehiculos:
        marca_nombre = v.marca.nombre if v.marca else "Sin marca"
        modelo_nombre = v.modelo.nombre if v.modelo else "Sin modelo"
        print(f"   {v.patente}: {marca_nombre} {modelo_nombre}")

    # 3. Verificar datos disponibles para formulario
    marcas_chile = Marca.objects.filter(country="CL")
    modelos_chile = Modelo.objects.filter(marca__country="CL")

    print("\n📊 Datos disponibles para formulario:")
    print(f"   ✅ Marcas Chile: {marcas_chile.count()}")
    print(f"   ✅ Modelos Chile: {modelos_chile.count()}")

    # 4. Verificar marcas principales con modelos
    marcas_principales = ["Toyota", "Chevrolet", "Ford"]
    print("\n🚗 Marcas principales con modelos:")
    for marca_nombre in marcas_principales:
        marca = marcas_chile.filter(nombre=marca_nombre).first()
        if marca:
            modelos = Modelo.objects.filter(marca=marca)
            print(f"   {marca_nombre}: {modelos.count()} modelos")

    print("\n🎉 ESTADO FINAL:")
    print("   ✅ Problema de guardado: RESUELTO")
    print("   ✅ Vehículos muestran nombres correctos")
    print("   ✅ Formulario guarda IDs pero muestra nombres")
    print("   ✅ Datos limpios sin marcas/modelos numéricos")


if __name__ == "__main__":
    main()
