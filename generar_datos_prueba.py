#!/usr/bin/env python
"""
Script para generar documentos de prueba (versión corregida).
Genera documentos con repuestos, servicios y otros servicios usando los modelos
lineales: LineaRepuesto, LineaServicio, LineaOtroServicio.
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.tecnico import Tecnico
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaServicio, LineaRepuesto, LineaOtroServicio
from taller.models.repuesto import Repuesto
from taller.models.tienda import Tienda
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.extras_vehiculo import ColorVehiculo
from taller.servicios.models import Servicio


def crear_datos_prueba():
    print("🚀 Creando documentos de prueba...")

    usuario = User.objects.first()
    if not usuario:
        print("❌ No hay usuarios en el sistema")
        return

    empresa, _ = Empresa.objects.get_or_create(defaults={'nombre_taller': 'Taller Demo'})
    print(f"✅ Empresa: {empresa.nombre_taller}")

    # Técnicos
    tecnicos_data = [
        "Juan Pérez", "María González", "Carlos Rodríguez",
        "Ana Martínez", "Luis Silva", "Carmen López"
    ]
    tecnicos = []
    for nombre in tecnicos_data:
        tecnico, _ = Tecnico.objects.get_or_create(
            nombre=nombre,
            empresa=empresa,
            defaults={
                'telefono': f"+569{random.randint(10000000, 99999999)}",
                'direccion': f"Dirección {nombre}",
                'activo': True
            }
        )
        tecnicos.append(tecnico)

    # Clientes
    clientes_data = [
        ("Pedro", "Sánchez", "pedro.sanchez@email.com"),
        ("Lucía", "Morales", "lucia.morales@email.com"),
        ("Roberto", "Fernández", "roberto.fernandez@email.com"),
        ("Elena", "Torres", "elena.torres@email.com"),
        ("Miguel", "Castro", "miguel.castro@email.com"),
        ("Isabel", "Vargas", "isabel.vargas@email.com"),
        ("Jorge", "Herrera", "jorge.herrera@email.com"),
        ("Patricia", "Mendoza", "patricia.mendoza@email.com"),
    ]
    clientes = []
    for nombre, apellido, email in clientes_data:
        cliente, _ = Cliente.objects.get_or_create(
            nombre=nombre,
            apellido=apellido,
            empresa=empresa,
            defaults={
                'telefono': f"+569{random.randint(10000000, 99999999)}",
                'email': email,
                'direccion': f"Calle {nombre} {apellido} 123"
            }
        )
        clientes.append(cliente)

    # Marcas, modelos y colores disponibles
    marcas_disponibles = list(Marca.objects.all()[:20])
    colores_disponibles = list(ColorVehiculo.objects.all())

    vehiculos = []
    vehiculos_data = [
        ("ABCD12", 2020), ("EFGH34", 2019), ("IJKL56", 2021), ("MNOP78", 2018),
        ("QRST90", 2022), ("UVWX12", 2017), ("YZAB34", 2020), ("CDEF56", 2019),
    ]
    for i, (patente, anio) in enumerate(vehiculos_data):
        if i < len(clientes) and marcas_disponibles:
            marca = random.choice(marcas_disponibles)
            modelos_marca = list(Modelo.objects.filter(marca=marca))
            modelo = random.choice(modelos_marca) if modelos_marca else None
            color = random.choice(colores_disponibles) if colores_disponibles else None
            vehiculo, _ = Vehiculo.objects.get_or_create(
                patente=patente,
                cliente=clientes[i],
                empresa=empresa,
                defaults={
                    'marca': marca,
                    'modelo': modelo,
                    'anio': anio,
                    'color': color,
                    'vin': f"VIN{random.randint(100000, 999999)}"
                }
            )
            vehiculos.append(vehiculo)

    # Tienda
    tienda, _ = Tienda.objects.get_or_create(
        empresa=empresa,
        nombre="Tienda Principal",
        defaults={
            'direccion': 'Dirección Principal 123',
            'telefono': '+56912345678',
            'email': 'tienda@taller.com',
            'activo': True
        }
    )

    # Repuestos de ejemplo
    repuestos_data = [
        ("FLT001", "Filtro de aceite", 15000, 12000),
        ("FLT002", "Filtro de aire", 25000, 20000),
        ("FLT003", "Filtro de combustible", 35000, 28000),
        ("BRK001", "Pastillas de freno delanteras", 45000, 35000),
        ("BRK002", "Pastillas de freno traseras", 35000, 28000),
        ("OIL001", "Aceite motor 5W30", 28000, 22000),
        ("SPK001", "Bujías NGK", 8000, 6000),
        ("TIR001", "Neumático 185/65R15", 85000, 65000),
        ("BAT001", "Batería 12V 65Ah", 120000, 95000),
        ("LMP001", "Ampolleta H4", 12000, 9000),
    ]
    repuestos = []
    for partnumber, nombre, precio_venta, precio_compra in repuestos_data:
        repuesto, _ = Repuesto.objects.get_or_create(
            part_number=partnumber,
            tienda=tienda,
            defaults={
                'nombre_repuesto': nombre,
                'precio_venta': precio_venta,
                'precio_compra': precio_compra,
                'stock': random.randint(1, 50),
                'observaciones': f"Repuesto {nombre}",
                'empresa': empresa
            }
        )
        repuestos.append(repuesto)

    servicios = list(Servicio.objects.filter(activo=True)[:15])

    tipos_documento = ["Presupuesto", "Orden de trabajo", "Factura"]
    documentos_creados = 0

    for tipo in tipos_documento:
        print(f"\n📋 Creando 10 documentos tipo: {tipo}")
        for i in range(10):
            try:
                cliente = random.choice(clientes)
                vehiculo = random.choice([v for v in vehiculos if v.cliente == cliente]) if vehiculos else None
                tecnico = random.choice(tecnicos)

                documento = Documento.objects.create(
                    empresa=empresa,
                    tipo_documento=tipo,
                    numero_documento=f"{tipo[:3].upper()}-{random.randint(10000, 99999)}",
                    cliente=cliente,
                    vehiculo=vehiculo,
                    tecnico=tecnico,
                    kilometraje=random.randint(5000, 200000),
                    observaciones=f"Documento de prueba {tipo} #{i+1}.",
                    incluir_iva=random.choice([True, False]),
                    fecha=datetime.now().date() - timedelta(days=random.randint(0, 30))
                )

                # Repuestos
                for _ in range(random.randint(1, 4)):
                    repuesto = random.choice(repuestos)
                    cantidad = random.randint(1, 3)
                    precio_unitario = max(1000, repuesto.precio_venta + random.randint(-3000, 10000))
                    LineaRepuesto.objects.create(
                        documento=documento,
                        repuesto=repuesto,
                        cantidad=cantidad,
                        precio_unitario=precio_unitario,
                        codigo=repuesto.part_number,
                        nombre=repuesto.nombre_repuesto
                    )

                # Servicios
                if servicios:
                    for servicio in random.sample(servicios, random.randint(1, min(3, len(servicios)))):
                        precio_base = getattr(servicio, 'precio_base', None) or 25000
                        precio = max(5000, int(precio_base) + random.randint(-5000, 15000))
                        LineaServicio.objects.create(
                            empresa=empresa,
                            documento=documento,
                            nombre=getattr(servicio, 'get_label', lambda: str(servicio))() if hasattr(servicio, 'get_label') else str(servicio),
                            precio_unitario=precio
                        )

                # Otros servicios
                for _ in range(random.randint(0, 2)):
                    servicio_base = random.choice(servicios) if servicios else None
                    if servicio_base:
                        precio_cliente = random.randint(25000, 60000)
                        costo_interno = random.randint(15000, 40000)
                        LineaOtroServicio.objects.create(
                            documento=documento,
                            servicio=servicio_base,
                            nombre=f"Servicio externo - {getattr(servicio_base, 'get_label', lambda: str(servicio_base))()}",
                            empresa_externa=random.choice(["Empresa Externa SA", "Proveedor XYZ", "Servicios Técnicos Ltda"]),
                            costo_interno=costo_interno,
                            precio_cliente=precio_cliente,
                            observaciones=f"Servicio subcontratado especializado"
                        )

                documentos_creados += 1
                print(f"  ✅ Documento {i+1}/10 - {documento.numero_documento}")
            except Exception as e:
                print(f"  ❌ Error creando documento {i+1}: {e}")

    print(f"\n🎉 ¡Proceso completado!")
    print(f"📊 Documentos creados: {documentos_creados}")


if __name__ == "__main__":
    crear_datos_prueba()
