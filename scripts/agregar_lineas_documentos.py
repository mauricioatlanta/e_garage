#!/usr/bin/env python
"""
Script para agregar líneas de repuestos y servicios a los documentos existentes
"""

import os
import sys
from decimal import Decimal

import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.documento import Documento
from taller.models.lineas_documento import (
    LineaOtroServicio,
    LineaRepuesto,
    LineaServicio,
)
from taller.models.repuesto import Repuesto
from taller.servicios.models import Servicio


def agregar_lineas_documentos():
    print("💰 Agregando líneas de repuestos y servicios a documentos existentes...")

    # Obtener todos los documentos
    documentos = Documento.objects.all()

    if not documentos:
        print(
            "❌ No hay documentos en el sistema. Ejecuta primero crear_datos_prueba_i18n_simple.py"
        )
        return

    print(f"📄 Encontrados {documentos.count()} documentos")

    for doc in documentos:
        print(f"\n📋 Procesando documento: {doc.numero_documento} ({doc.get_tipo_display()})")

        # Verificar si ya tiene líneas
        if doc.lineas_repuesto.exists() or doc.lineas_servicio.exists():
            print("   ⚠️ Documento ya tiene líneas, saltando...")
            continue

        empresa = doc.empresa

        # Crear servicios si no existen
        if empresa.pais == "CL":
            # Servicios para Chile
            servicio_aceite, created = Servicio.objects.get_or_create(
                nombre="Cambio de aceite y filtros",
                empresa=empresa,
                defaults={
                    "descripcion": "Cambio de aceite motor, filtro de aceite y filtro de aire",
                    "precio": Decimal("35000"),
                    "tipo": "interno",
                    "tiempo_estimado": 60,
                },
            )

            servicio_alineacion, created = Servicio.objects.get_or_create(
                nombre="Alineación y balanceo",
                empresa=empresa,
                defaults={
                    "descripcion": "Alineación de dirección y balanceo de ruedas",
                    "precio": Decimal("25000"),
                    "tipo": "interno",
                    "tiempo_estimado": 90,
                },
            )

        else:  # USA
            # Servicios para USA
            servicio_aceite, created = Servicio.objects.get_or_create(
                nombre="Oil Change Service",
                empresa=empresa,
                defaults={
                    "descripcion": "Complete oil change with filter replacement",
                    "precio": Decimal("89.99"),
                    "tipo": "interno",
                    "tiempo_estimado": 60,
                },
            )

            servicio_alineacion, created = Servicio.objects.get_or_create(
                nombre="Wheel Alignment & Balance",
                empresa=empresa,
                defaults={
                    "descripcion": "Professional wheel alignment and tire balancing",
                    "precio": Decimal("125.00"),
                    "tipo": "interno",
                    "tiempo_estimado": 90,
                },
            )

        # Crear repuestos si no existen
        if empresa.pais == "CL":
            # Repuestos para Chile
            repuesto_aceite, created = Repuesto.objects.get_or_create(
                codigo="ACE-001-CL",
                empresa=empresa,
                defaults={
                    "nombre": "Aceite motor 15W-40",
                    "descripcion": "Aceite mineral para motor gasolina/diesel",
                    "precio_compra": Decimal("8500"),
                    "precio_venta": Decimal("12000"),
                    "stock": 25,
                },
            )

            repuesto_filtro, created = Repuesto.objects.get_or_create(
                codigo="FIL-001-CL",
                empresa=empresa,
                defaults={
                    "nombre": "Filtro de aceite",
                    "descripcion": "Filtro de aceite universal",
                    "precio_compra": Decimal("3500"),
                    "precio_venta": Decimal("6500"),
                    "stock": 50,
                },
            )

        else:  # USA
            # Repuestos para USA
            repuesto_aceite, created = Repuesto.objects.get_or_create(
                codigo="OIL-001-US",
                empresa=empresa,
                defaults={
                    "nombre": "Synthetic Motor Oil 5W-30",
                    "descripcion": "Premium synthetic motor oil",
                    "precio_compra": Decimal("24.99"),
                    "precio_venta": Decimal("39.99"),
                    "stock": 30,
                },
            )

            repuesto_filtro, created = Repuesto.objects.get_or_create(
                codigo="FIL-001-US",
                empresa=empresa,
                defaults={
                    "nombre": "Oil Filter",
                    "descripcion": "High-performance oil filter",
                    "precio_compra": Decimal("8.99"),
                    "precio_venta": Decimal("16.99"),
                    "stock": 40,
                },
            )

        # Agregar líneas de servicio al documento
        print("   🛠️ Agregando servicios...")
        LineaServicio.objects.create(
            documento=doc,
            servicio=servicio_aceite,
            nombre=servicio_aceite.nombre,
            cantidad=1,
            precio_unitario=servicio_aceite.precio,
            descuento=Decimal("0.00"),
        )

        LineaServicio.objects.create(
            documento=doc,
            servicio=servicio_alineacion,
            nombre=servicio_alineacion.nombre,
            cantidad=1,
            precio_unitario=servicio_alineacion.precio,
            descuento=Decimal("5.00"),  # 5% descuento
        )

        # Agregar líneas de repuesto al documento
        print("   🔧 Agregando repuestos...")
        LineaRepuesto.objects.create(
            documento=doc,
            repuesto=repuesto_aceite,
            codigo=repuesto_aceite.codigo,
            nombre=repuesto_aceite.nombre,
            cantidad=4,  # 4 litros de aceite
            precio_unitario=repuesto_aceite.precio_venta,
            descuento=Decimal("0.00"),
        )

        LineaRepuesto.objects.create(
            documento=doc,
            repuesto=repuesto_filtro,
            codigo=repuesto_filtro.codigo,
            nombre=repuesto_filtro.nombre,
            cantidad=1,
            precio_unitario=repuesto_filtro.precio_venta,
            descuento=Decimal("0.00"),
        )

        # Agregar servicio externo (subcontratado)
        print("   🏢 Agregando servicio externo...")
        if empresa.pais == "CL":
            LineaOtroServicio.objects.create(
                documento=doc,
                nombre="Reparación de radiador",
                empresa_externa="Radiadores Chile Ltda.",
                cantidad=1,
                costo_interno=Decimal("45000"),
                precio_cliente=Decimal("65000"),
            )
        else:
            LineaOtroServicio.objects.create(
                documento=doc,
                nombre="AC System Repair",
                empresa_externa="Miami AC Solutions LLC",
                cantidad=1,
                costo_interno=Decimal("150.00"),
                precio_cliente=Decimal("225.00"),
            )

        # Calcular totales
        total_repuestos = doc.total_repuestos()
        total_servicios = doc.total_servicios()
        total_otros = doc.total_otros_servicios()
        total_general = doc.total_general()

        print("   💰 Totales calculados:")
        print(f"      Repuestos: {total_repuestos}")
        print(f"      Servicios: {total_servicios}")
        print(f"      Otros servicios: {total_otros}")
        print(f"      Total general: {total_general}")

    print("\n✅ ¡Líneas agregadas a todos los documentos!")

    # Mostrar resumen
    total_docs = Documento.objects.count()
    total_lineas_repuesto = LineaRepuesto.objects.count()
    total_lineas_servicio = LineaServicio.objects.count()
    total_lineas_otros = LineaOtroServicio.objects.count()

    print("\n📊 Resumen:")
    print(f"   📄 Documentos: {total_docs}")
    print(f"   🔧 Líneas de repuestos: {total_lineas_repuesto}")
    print(f"   🛠️ Líneas de servicios: {total_lineas_servicio}")
    print(f"   🏢 Líneas otros servicios: {total_lineas_otros}")

    print("\n🎉 Ahora los documentos deberían mostrar los totales correctos en el listado!")


if __name__ == "__main__":
    agregar_lineas_documentos()
