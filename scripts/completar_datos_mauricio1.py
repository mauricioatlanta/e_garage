#!/usr/bin/env python
"""
Script para crear repuestos específicos para mauricio1 y luego generar más documentos completos
"""

import os
import random
import sys
from datetime import datetime, timedelta

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.lineas_documento import (
    LineaOtroServicio,
    LineaRepuesto,
    LineaServicio,
)

# Nota: usamos LineaRepuesto/LineaServicio/LineaOtroServicio como modelos canónicos
from taller.models.repuesto import Repuesto
from taller.models.tecnico import Tecnico
from taller.models.tienda import Tienda
from taller.models.vehiculos import Vehiculo
from taller.servicios.models import Servicio


def crear_repuestos_y_documentos_mauricio1():
    print("🚀 Creando repuestos y documentos completos para mauricio1...")

    # Obtener usuario y empresa
    usuario = User.objects.get(username="mauricio1")
    empresa = Empresa.objects.get(user=usuario)

    # Crear tienda si no existe
    tienda, created = Tienda.objects.get_or_create(
        empresa=empresa,
        nombre="Tienda Principal Mauricio1",
        defaults={
            "direccion": "Calle Principal 123",
            "telefono": "+56912345678",
            "email": "tienda@mauricio1.com",
            "activo": True,
        },
    )
    print(f"✅ Tienda: {tienda.nombre}")

    # Crear repuestos específicos para mauricio1
    repuestos_data = [
        ("FLT001", "Filtro de aceite Toyota", 18000, 14000),
        ("FLT002", "Filtro de aire Honda", 22000, 18000),
        ("FLT003", "Filtro combustible universal", 28000, 22000),
        ("BRK001", "Pastillas freno delanteras", 42000, 32000),
        ("BRK002", "Pastillas freno traseras", 38000, 28000),
        ("OIL001", "Aceite motor 5W30 4L", 32000, 26000),
        ("SPK001", "Bujías NGK platinum", 12000, 9000),
        ("TIR001", "Neumático 185/65R15", 92000, 72000),
        ("BAT001", "Batería 12V 70Ah", 145000, 115000),
        ("LMP001", "Ampolleta H4 LED", 15000, 11000),
        ("BEL001", "Correa distribución", 65000, 48000),
        ("FLU001", "Líquido frenos DOT4", 25000, 19000),
    ]

    repuestos = []
    for partnumber, nombre, precio_venta, precio_compra in repuestos_data:
        repuesto, created = Repuesto.objects.get_or_create(
            part_number=partnumber,
            tienda=tienda,
            defaults={
                "nombre_repuesto": nombre,
                "precio_venta": precio_venta,
                "precio_compra": precio_compra,
                "stock": random.randint(5, 50),
                "observaciones": f"Repuesto {nombre} para taller mauricio1",
                "empresa": empresa,
            },
        )
        repuestos.append(repuesto)

    print(f"✅ Repuestos creados: {len(repuestos)}")

    # Obtener datos existentes
    clientes = list(Cliente.objects.filter(empresa=empresa))
    vehiculos = list(Vehiculo.objects.filter(empresa=empresa))
    tecnicos = list(Tecnico.objects.filter(empresa=empresa))
    servicios = list(Servicio.objects.filter(activo=True)[:15])

    # Crear 5 documentos adicionales más completos de cada tipo
    tipos_documento = ["Presupuesto", "Orden de trabajo", "Factura"]

    documentos_creados = 0

    for tipo in tipos_documento:
        print(f"\n📋 Creando 5 documentos {tipo} con repuestos:")

        for i in range(5):
            try:
                cliente = random.choice(clientes)
                vehiculos_cliente = [v for v in vehiculos if v.cliente == cliente]

                if not vehiculos_cliente:
                    vehiculo = random.choice(vehiculos)
                    vehiculo.cliente = cliente
                    vehiculo.save()
                else:
                    vehiculo = random.choice(vehiculos_cliente)

                tecnico = random.choice(tecnicos)

                # Crear documento
                documento = Documento.objects.create(
                    empresa=empresa,
                    tipo_documento=tipo,
                    numero_documento=f"{tipo[:3].upper()}-{random.randint(50000, 99999)}",
                    cliente=cliente,
                    vehiculo=vehiculo,
                    tecnico=tecnico,
                    kilometraje=random.randint(10000, 250000),
                    observaciones=f"Documento completo {tipo} #{i+1} con repuestos y servicios. Cliente: {cliente.nombre}. Vehículo: {vehiculo.patente}.",
                    incluir_iva=random.choice([True, False]),
                    fecha=datetime.now().date() - timedelta(days=random.randint(0, 45)),
                )

                # Agregar 2-4 repuestos
                num_repuestos = random.randint(2, 4)
                repuestos_elegidos = random.sample(repuestos, num_repuestos)
                for repuesto in repuestos_elegidos:
                    cantidad = random.randint(1, 2)
                    precio = max(
                        1000, repuesto.precio_venta + random.randint(-2000, 8000)
                    )

                    LineaRepuesto.objects.create(
                        documento=documento,
                        repuesto=repuesto,
                        cantidad=cantidad,
                        precio_unitario=precio,
                        codigo=repuesto.part_number,
                        nombre=repuesto.nombre_repuesto,
                    )

                # Agregar 1-3 servicios
                num_servicios = random.randint(1, 3)
                servicios_elegidos = random.sample(servicios, num_servicios)
                for servicio in servicios_elegidos:
                    precio_base = servicio.precio_base or 30000
                    precio = max(8000, int(precio_base) + random.randint(-5000, 20000))

                    LineaServicio.objects.create(
                        empresa=empresa,
                        documento=documento,
                        nombre=servicio.get_label(),
                        precio_unitario=precio,
                    )

                # Agregar otro servicio ocasionalmente
                if random.choice([True, False, False]):  # 33% probabilidad
                    servicio_base = random.choice(servicios)
                    precio_cliente = random.randint(30000, 80000)
                    costo_interno = random.randint(20000, 50000)

                    LineaOtroServicio.objects.create(
                        documento=documento,
                        servicio=servicio_base,
                        nombre=f"Servicio especializado - {servicio_base.get_label()}",
                        empresa_externa=random.choice(
                            [
                                "Taller Especializado Los Andes",
                                "Servicios Automotrices Premium",
                                "Mecánica Avanzada Chile",
                                "Centro de Diagnóstico Pro",
                            ]
                        ),
                        costo_interno=costo_interno,
                        precio_cliente=precio_cliente,
                        observaciones=f"Servicio especializado subcontratado para {tipo}",
                    )

                documentos_creados += 1
                print(f"  ✅ {tipo} {i+1}/5 - {documento.numero_documento}")

            except Exception as e:
                print(f"  ❌ Error creando {tipo} {i+1}: {e}")

    print("\n🎉 ¡Proceso completado!")
    print(f"📊 Documentos adicionales creados: {documentos_creados}")

    # Estadísticas finales
    print(f"\n📊 Estadísticas finales para empresa '{empresa.nombre_taller}':")
    for tipo in tipos_documento:
        count = Documento.objects.filter(tipo_documento=tipo, empresa=empresa).count()
        print(f"  - {tipo}: {count}")

    print("\n📈 Totales generales:")
    print(f"  - Total documentos: {Documento.objects.filter(empresa=empresa).count()}")
    from taller.models.lineas_documento import LineaOtroServicio, LineaRepuesto

    print(
        f"  - Total repuestos en docs: {LineaRepuesto.objects.filter(documento__empresa=empresa).count()}"
    )
    print(
        f"  - Total servicios en docs: {LineaServicio.objects.filter(documento__empresa=empresa).count()}"
    )
    print(
        f"  - Total otros servicios: {LineaOtroServicio.objects.filter(documento__empresa=empresa).count()}"
    )
    print(
        f"  - Total repuestos disponibles: {Repuesto.objects.filter(empresa=empresa).count()}"
    )


if __name__ == "__main__":
    crear_repuestos_y_documentos_mauricio1()
