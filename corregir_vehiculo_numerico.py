#!/usr/bin/env python
"""
Script para corregir el vehículo con datos numéricos problemáticos
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
    print("🔧 CORRECCIÓN: Vehículo con datos numéricos\n")

    # Encontrar el vehículo problemático
    try:
        vehiculo = Vehiculo.objects.get(patente="CCWH63")
        print(f"📍 Vehículo encontrado: {vehiculo.patente}")
        print(f"   Marca actual: {vehiculo.marca} (ID: {vehiculo.marca_id})")
        print(f"   Modelo actual: {vehiculo.modelo} (ID: {vehiculo.modelo_id})")

        # Buscar Toyota Corolla para reemplazar
        toyota = Marca.objects.filter(nombre="Toyota", country="CL").first()
        if toyota:
            corolla = Modelo.objects.filter(nombre="Corolla", marca=toyota).first()

            if toyota and corolla:
                print(f"\n✅ Asignando marca y modelo correctos:")
                print(f"   Nueva marca: {toyota.nombre} (ID: {toyota.id})")
                print(f"   Nuevo modelo: {corolla.nombre} (ID: {corolla.id})")

                # Actualizar el vehículo
                vehiculo.marca = toyota
                vehiculo.modelo = corolla
                vehiculo.save()

                print(f"✅ Vehículo actualizado: {vehiculo}")

                # Limpiar marcas y modelos numéricos huérfanos
                print(f"\n🧹 Limpiando datos numéricos huérfanos:")

                # Eliminar modelo numérico
                modelo_numerico = Modelo.objects.filter(nombre="38").first()
                if modelo_numerico:
                    print(f"   🗑️  Eliminando modelo '{modelo_numerico.nombre}'")
                    modelo_numerico.delete()

                # Eliminar marca numérica
                marca_numerica = Marca.objects.filter(nombre="8").first()
                if marca_numerica:
                    print(f"   🗑️  Eliminando marca '{marca_numerica.nombre}'")
                    marca_numerica.delete()

                print(f"\n🎉 CORRECCIÓN COMPLETADA")
                print(f"   ✅ Vehículo CCWH63 ahora es: {vehiculo}")
                print(f"   ✅ Datos numéricos problemáticos eliminados")

            else:
                print(f"❌ Error: No se encontró Toyota Corolla para Chile")
        else:
            print(f"❌ Error: No se encontró marca Toyota para Chile")

    except Vehiculo.DoesNotExist:
        print(f"❌ Error: Vehículo CCWH63 no encontrado")


if __name__ == "__main__":
    main()
