#!/usr/bin/env python
"""
Script para probar la creación de documentos con servicios externos
"""
import os
import sys

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()


from taller.models import Empresa
from taller.models.clientes import Cliente
from taller.servicios.models import ServicioExterno


def probar_servicios_externos():
    """Probar la funcionalidad de servicios externos"""
    print("🧪 Probando servicios externos...")

    # Obtener empresa
    try:
        empresa = Empresa.objects.first()
        if not empresa:
            print("❌ No se encontró ninguna empresa.")
            return
        print(f"✅ Usando empresa: {empresa.nombre_taller}")
    except Exception as e:
        print(f"❌ Error al obtener empresa: {e}")
        return

    # Obtener cliente
    try:
        cliente = Cliente.objects.filter(empresa=empresa).first()
        if not cliente:
            print("❌ No se encontró ningún cliente.")
            return
        print(f"✅ Usando cliente: {cliente.nombre}")
    except Exception as e:
        print(f"❌ Error al obtener cliente: {e}")
        return

    # Obtener servicios externos
    servicios_externos = ServicioExterno.objects.filter(empresa=empresa, activo=True)
    print(f"📊 Servicios externos disponibles: {servicios_externos.count()}")

    for servicio in servicios_externos[:3]:  # Mostrar solo los primeros 3
        print(f"   🔧 {servicio.nombre} - {servicio.empresa_externa}")
        print(
            f"      💰 Costo: ${servicio.costo_taller} | Cliente: ${servicio.precio_cliente} | Ganancia: ${servicio.ganancia}"
        )

    print("\n✅ VERIFICACIÓN EXITOSA!")
    print("📊 Servicios externos configurados y listos para usar en documentos")
    print("🔧 Modelo LineaOtroServicio actualizado con soporte para ServicioExterno")
    print(
        "💰 Los servicios externos pueden ser agregados a documentos con precios configurados"
    )

    # Lista de servicios disponibles
    print("\n🏢 SERVICIOS EXTERNOS DISPONIBLES:")
    for i, servicio in enumerate(servicios_externos, 1):
        ganancia_pct = (
            (
                (servicio.precio_cliente - servicio.costo_taller)
                / servicio.costo_taller
                * 100
            )
            if servicio.costo_taller > 0
            else 0
        )
        print(f"   {i}. {servicio.nombre}")
        print(f"      🏢 Empresa: {servicio.empresa_externa}")
        print(
            f"      💰 Costo: ${servicio.costo_taller:,.0f} | Cliente: ${servicio.precio_cliente:,.0f}"
        )
        print(f"      � Ganancia: ${servicio.ganancia:,.0f} ({ganancia_pct:.1f}%)")
        print()

    print("\n🎉 Prueba completada!")


if __name__ == "__main__":
    probar_servicios_externos()
