#!/usr/bin/env python
"""
Script para crear servicios externos de prueba
"""

import os
import sys

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from decimal import Decimal

from taller.models import Empresa
from taller.servicios.models import CategoriaServicio, ServicioExterno


def crear_servicios_externos():
    """Crear servicios externos de prueba"""
    print("🔧 Creando servicios externos de prueba...")

    # Obtener empresa (asumiendo que existe al menos una)
    try:
        empresa = Empresa.objects.first()
        if not empresa:
            print("❌ No se encontró ninguna empresa. Primero crea una empresa.")
            return
    except Exception as e:
        print(f"❌ Error al obtener empresa: {e}")
        return

    # Obtener o crear categorías
    try:
        categoria, created = CategoriaServicio.objects.get_or_create(
            country="CL",
            code="servicios_externos",
        )
        if created:
            print(f"✅ Categoría creada: {categoria}")
    except Exception as e:
        print(f"⚠️ Error con categoría: {e}")
        categoria = CategoriaServicio.objects.first()

    # Servicios externos a crear
    servicios_data = [
        {
            "nombre": "Lavado y Encerado Premium",
            "empresa_externa": "AutoLavado Premium SpA",
            "costo_taller": Decimal("15000"),
            "precio_cliente": Decimal("25000"),
            "descripcion": "Lavado completo, encerado y limpieza interior profesional",
            "tiempo_estimado": "2-3 horas",
        },
        {
            "nombre": "Polarizado de Vidrios",
            "empresa_externa": "Polarizados Chile Ltda",
            "costo_taller": Decimal("80000"),
            "precio_cliente": Decimal("120000"),
            "descripcion": "Polarizado completo de vidrios con garantía de 5 años",
            "tiempo_estimado": "3-4 horas",
        },
        {
            "nombre": "Instalación de Audio y Video",
            "empresa_externa": "AudioCar Professional",
            "costo_taller": Decimal("120000"),
            "precio_cliente": Decimal("180000"),
            "descripcion": "Instalación profesional de sistema de audio y video",
            "tiempo_estimado": "4-6 horas",
        },
        {
            "nombre": "Tapizado y Restauración Interior",
            "empresa_externa": "Tapicería Automotriz Deluxe",
            "costo_taller": Decimal("200000"),
            "precio_cliente": Decimal("300000"),
            "descripcion": "Restauración completa de tapizado interior",
            "tiempo_estimado": "1-2 días",
        },
        {
            "nombre": "Pintura y Carrocería",
            "empresa_externa": "Maestranza Automotriz Central",
            "costo_taller": Decimal("350000"),
            "precio_cliente": Decimal("500000"),
            "descripcion": "Reparación y pintura de carrocería profesional",
            "tiempo_estimado": "3-5 días",
        },
        {
            "nombre": "Alineación y Balanceo Premium",
            "empresa_externa": "Neumáticos y Servicios Pro",
            "costo_taller": Decimal("25000"),
            "precio_cliente": Decimal("35000"),
            "descripcion": "Alineación computarizada y balanceo de alta precisión",
            "tiempo_estimado": "1-2 horas",
        },
        {
            "nombre": "Instalación de GNC/GLP",
            "empresa_externa": "EcoGas Automotriz",
            "costo_taller": Decimal("180000"),
            "precio_cliente": Decimal("250000"),
            "descripción": "Instalación completa de sistema de gas natural comprimido",
            "tiempo_estimado": "1 día",
        },
        {
            "nombre": "Blindaje Automotriz",
            "empresa_externa": "Seguridad Vehicular Ltda",
            "costo_taller": Decimal("800000"),
            "precio_cliente": Decimal("1200000"),
            "descripcion": "Blindaje profesional nivel 3A para vehículos",
            "tiempo_estimado": "1-2 semanas",
        },
    ]

    servicios_creados = []

    for data in servicios_data:
        try:
            servicio, created = ServicioExterno.objects.get_or_create(
                empresa=empresa,
                nombre=data["nombre"],
                empresa_externa=data["empresa_externa"],
                defaults={
                    "categoria": categoria,
                    "costo_taller": data["costo_taller"],
                    "precio_cliente": data["precio_cliente"],
                    "descripcion": data["descripcion"],
                    "tiempo_estimado": data["tiempo_estimado"],
                    "activo": True,
                },
            )

            if created:
                servicios_creados.append(servicio)
                print(f"✅ Servicio externo creado: {servicio.nombre} - {servicio.empresa_externa}")
                print(
                    f"   💰 Costo: ${servicio.costo_taller} | Cliente: ${servicio.precio_cliente} | Ganancia: ${servicio.ganancia}"
                )
            else:
                print(f"⚠️ Servicio ya existe: {servicio.nombre}")

        except Exception as e:
            print(f"❌ Error creando servicio {data['nombre']}: {e}")

    print("\n🎉 Proceso completado!")
    print(f"📊 Servicios externos creados: {len(servicios_creados)}")
    print(f"📊 Total servicios externos: {ServicioExterno.objects.filter(empresa=empresa).count()}")

    # Mostrar estadísticas
    if servicios_creados:
        total_ganancia = sum(s.ganancia for s in servicios_creados)
        print(f"💰 Ganancia potencial total: ${total_ganancia:,.0f}")


if __name__ == "__main__":
    crear_servicios_externos()
