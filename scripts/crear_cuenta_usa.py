#!/usr/bin/env python
"""
Script para crear cuenta de prueba para USA y generar datos completos
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
from taller.models.documento import (
    Documento,
    OtroServicioDocumento,
    RepuestoDocumento,
    ServicioDocumento,
)
from taller.models.empresa import Empresa
from taller.models.extras_vehiculo import ColorVehiculo
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.repuesto import Repuesto
from taller.models.tecnico import Tecnico
from taller.models.tienda import Tienda
from taller.models.vehiculos import Vehiculo
from taller.servicios.models import Servicio


def crear_cuenta_usa_completa():
    print("🇺🇸 Creando cuenta de prueba para USA...")

    # Crear usuario para USA
    username_usa = "testuser_usa"
    password_usa = "TestUSA2025!"
    email_usa = "testuser@usa-garage.com"

    try:
        # Verificar si ya existe
        usuario_usa = User.objects.get(username=username_usa)
        print(f"✅ Usuario {username_usa} ya existe")
    except User.DoesNotExist:
        # Crear nuevo usuario
        usuario_usa = User.objects.create_user(
            username=username_usa,
            password=password_usa,
            email=email_usa,
            first_name="Test",
            last_name="USA User",
        )
        print(f"✅ Usuario creado: {username_usa}")

    # Crear empresa para USA
    try:
        empresa_usa = Empresa.objects.get(user=usuario_usa)
        print(f"✅ Empresa ya existe: {empresa_usa.nombre_taller}")
    except Empresa.DoesNotExist:
        empresa_usa = Empresa.objects.create(
            user=usuario_usa,
            nombre_taller="USA Test Garage",
            empresa="USA Test Garage LLC",
            direccion="123 Main Street, New York, NY 10001",
            telefono="+1-555-123-4567",
            email=email_usa,
            pais="US",  # Importante: país USA
            zona_horaria="America/New_York",
        )
        print(f"✅ Empresa creada: {empresa_usa.nombre_taller}")

    # Crear técnicos para USA
    tecnicos_usa_data = [
        ("John Smith", "+1-555-111-2222", "123 Tech Street, NY"),
        ("Sarah Johnson", "+1-555-333-4444", "456 Mechanic Ave, NY"),
        ("Mike Williams", "+1-555-555-6666", "789 Service Blvd, NY"),
    ]

    tecnicos_usa = []
    for nombre, telefono, direccion in tecnicos_usa_data:
        tecnico, created = Tecnico.objects.get_or_create(
            nombre=nombre,
            empresa=empresa_usa,
            defaults={"telefono": telefono, "direccion": direccion, "activo": True},
        )
        tecnicos_usa.append(tecnico)
    print(f"✅ Técnicos USA creados: {len(tecnicos_usa)}")

    # Crear clientes para USA
    clientes_usa_data = [
        ("Robert", "Anderson", "robert.anderson@email.com"),
        ("Jennifer", "Davis", "jennifer.davis@email.com"),
        ("Michael", "Wilson", "michael.wilson@email.com"),
        ("Lisa", "Martinez", "lisa.martinez@email.com"),
        ("David", "Taylor", "david.taylor@email.com"),
        ("Ashley", "Brown", "ashley.brown@email.com"),
        ("James", "Garcia", "james.garcia@email.com"),
        ("Emily", "Rodriguez", "emily.rodriguez@email.com"),
    ]

    clientes_usa = []
    for nombre, apellido, email in clientes_usa_data:
        cliente, created = Cliente.objects.get_or_create(
            nombre=nombre,
            apellido=apellido,
            empresa=empresa_usa,
            defaults={
                "telefono": f"+1-555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                "email": email,
                "direccion": f"{random.randint(100, 999)} {nombre} Street, NY 100{random.randint(10, 99)}",
            },
        )
        clientes_usa.append(cliente)
    print(f"✅ Clientes USA creados: {len(clientes_usa)}")

    # Crear vehículos para USA usando marcas y modelos existentes
    marcas_disponibles = list(Marca.objects.all()[:25])
    colores_disponibles = list(ColorVehiculo.objects.all())

    vehiculos_usa_data = [
        ("ABC1234", 2020),
        ("DEF5678", 2019),
        ("GHI9012", 2021),
        ("JKL3456", 2018),
        ("MNO7890", 2022),
        ("PQR1357", 2017),
        ("STU2468", 2020),
        ("VWX9753", 2019),
    ]

    vehiculos_usa = []
    for i, (patente, año) in enumerate(vehiculos_usa_data):
        if i < len(clientes_usa) and marcas_disponibles:
            marca = random.choice(marcas_disponibles)
            modelos_marca = list(Modelo.objects.filter(marca=marca))
            modelo = random.choice(modelos_marca) if modelos_marca else None
            color = random.choice(colores_disponibles) if colores_disponibles else None

            vehiculo, created = Vehiculo.objects.get_or_create(
                patente=patente,
                cliente=clientes_usa[i],
                empresa=empresa_usa,
                defaults={
                    "marca": marca,
                    "modelo": modelo,
                    "anio": año,
                    "color": color,
                    "vin": f"VIN{random.randint(100000, 999999)}",
                },
            )
            vehiculos_usa.append(vehiculo)
    print(f"✅ Vehículos USA creados: {len(vehiculos_usa)}")

    # Crear tienda para USA
    tienda_usa, created = Tienda.objects.get_or_create(
        empresa=empresa_usa,
        nombre="USA Main Parts Store",
        defaults={
            "direccion": "456 Parts Avenue, New York, NY 10002",
            "telefono": "+1-555-PARTS-1",
            "email": "parts@usa-garage.com",
            "activo": True,
        },
    )
    print(f"✅ Tienda USA: {tienda_usa.nombre}")

    # Crear repuestos para USA (precios en dólares convertidos a centavos para el sistema)
    repuestos_usa_data = [
        ("US-FLT001", "Oil Filter Toyota", 1500, 1200),  # $15.00
        ("US-FLT002", "Air Filter Honda", 2200, 1800),  # $22.00
        ("US-FLT003", "Fuel Filter Universal", 2800, 2200),  # $28.00
        ("US-BRK001", "Front Brake Pads", 4500, 3500),  # $45.00
        ("US-BRK002", "Rear Brake Pads", 3800, 2800),  # $38.00
        ("US-OIL001", "Motor Oil 5W30 4Q", 3200, 2600),  # $32.00
        ("US-SPK001", "NGK Platinum Spark Plugs", 1200, 900),  # $12.00
        ("US-TIR001", "Tire 185/65R15", 9500, 7500),  # $95.00
        ("US-BAT001", "12V 70Ah Battery", 14500, 11500),  # $145.00
        ("US-LMP001", "H4 LED Bulb", 1800, 1400),  # $18.00
        ("US-BEL001", "Timing Belt", 6800, 5200),  # $68.00
        ("US-FLU001", "DOT4 Brake Fluid", 2500, 1900),  # $25.00
    ]

    repuestos_usa = []
    for partnumber, nombre, precio_venta, precio_compra in repuestos_usa_data:
        repuesto, created = Repuesto.objects.get_or_create(
            part_number=partnumber,
            tienda=tienda_usa,
            defaults={
                "nombre_repuesto": nombre,
                "precio_venta": precio_venta,
                "precio_compra": precio_compra,
                "stock": random.randint(5, 50),
                "observaciones": f"USA part {nombre}",
                "empresa": empresa_usa,
            },
        )
        repuestos_usa.append(repuesto)
    print(f"✅ Repuestos USA creados: {len(repuestos_usa)}")

    # Obtener servicios existentes
    servicios = list(Servicio.objects.filter(activo=True)[:15])

    # Crear documentos para USA
    tipos_documento = ["Presupuesto", "Orden de trabajo", "Factura"]
    documentos_creados = 0

    for tipo in tipos_documento:
        print(f"\n📋 Creando 10 documentos USA tipo: {tipo}")

        for i in range(10):
            try:
                cliente = random.choice(clientes_usa)
                vehiculos_cliente = [v for v in vehiculos_usa if v.cliente == cliente]

                if not vehiculos_cliente:
                    vehiculo = random.choice(vehiculos_usa)
                    vehiculo.cliente = cliente
                    vehiculo.save()
                else:
                    vehiculo = random.choice(vehiculos_cliente)

                tecnico = random.choice(tecnicos_usa)

                # Crear documento
                documento = Documento.objects.create(
                    empresa=empresa_usa,
                    tipo_documento=tipo,
                    numero_documento=f"US-{tipo[:3].upper()}-{random.randint(10000, 99999)}",
                    cliente=cliente,
                    vehiculo=vehiculo,
                    tecnico=tecnico,
                    kilometraje=random.randint(5000, 200000),
                    observaciones=f"USA {tipo} document #{i+1}. Customer: {cliente.nombre} {cliente.apellido}. Vehicle: {vehiculo.patente}.",
                    incluir_iva=random.choice([True, False]),
                    fecha=datetime.now().date() - timedelta(days=random.randint(0, 30)),
                )

                # Agregar repuestos (2-4 por documento)
                num_repuestos = random.randint(2, 4)
                repuestos_elegidos = random.sample(repuestos_usa, num_repuestos)
                for repuesto in repuestos_elegidos:
                    cantidad = random.randint(1, 3)
                    precio = max(100, repuesto.precio_venta + random.randint(-200, 500))

                    RepuestoDocumento.objects.create(
                        documento=documento,
                        repuesto=repuesto,
                        cantidad=cantidad,
                        precio=precio,
                        codigo=repuesto.part_number,
                        nombre=repuesto.nombre_repuesto,
                    )

                # Agregar servicios (1-3 por documento)
                if servicios:
                    num_servicios = random.randint(1, 3)
                    servicios_elegidos = random.sample(servicios, num_servicios)
                    for servicio in servicios_elegidos:
                        precio_base = servicio.precio_base or 5000  # Precios más altos para USA
                        precio = max(1000, int(precio_base) + random.randint(-1000, 3000))

                        ServicioDocumento.objects.create(
                            empresa=empresa_usa,
                            documento=documento,
                            nombre=f"USA - {servicio.get_label()}",
                            precio=precio,
                        )

                # Agregar otros servicios ocasionalmente
                if servicios and random.choice([True, False]):
                    servicio_base = random.choice(servicios)
                    precio_cliente = random.randint(5000, 15000)  # Precios USA
                    costo_interno = random.randint(3000, 10000)

                    OtroServicioDocumento.objects.create(
                        documento=documento,
                        servicio=servicio_base,
                        nombre_servicio=f"USA External - {servicio_base.get_label()}",
                        empresa_externa=random.choice(
                            [
                                "Advanced Auto Services LLC",
                                "Premium Garage Solutions",
                                "NYC Auto Specialists Inc",
                                "Metropolitan Car Care",
                            ]
                        ),
                        costo_interno=costo_interno,
                        precio_cliente=precio_cliente,
                        observaciones=f"USA subcontracted service for {tipo}",
                    )

                documentos_creados += 1
                print(f"  ✅ {tipo} {i+1}/10 - {documento.numero_documento}")

            except Exception as e:
                print(f"  ❌ Error creating {tipo} {i+1}: {e}")

    print("\n🎉 ¡USA Account Setup Complete!")
    print(f"📊 Documents created: {documentos_creados}")

    # Mostrar credenciales
    print("\n🔑 USA TEST ACCOUNT CREDENTIALS:")
    print(f"   Username: {username_usa}")
    print(f"   Password: {password_usa}")
    print(f"   Email: {email_usa}")
    print(f"   Company: {empresa_usa.nombre_taller}")
    print("   Country: USA")

    # Estadísticas finales
    print(f"\n📊 Final Statistics for '{empresa_usa.nombre_taller}':")
    for tipo in tipos_documento:
        count = Documento.objects.filter(tipo_documento=tipo, empresa=empresa_usa).count()
        print(f"  - {tipo}: {count}")

    print("\n📈 Total USA Data:")
    print(f"  - Total documents: {Documento.objects.filter(empresa=empresa_usa).count()}")
    print(
        f"  - Total parts in docs: {RepuestoDocumento.objects.filter(documento__empresa=empresa_usa).count()}"
    )
    print(
        f"  - Total services in docs: {ServicioDocumento.objects.filter(empresa=empresa_usa).count()}"
    )
    print(
        f"  - Total other services: {OtroServicioDocumento.objects.filter(documento__empresa=empresa_usa).count()}"
    )
    print(f"  - Total parts available: {Repuesto.objects.filter(empresa=empresa_usa).count()}")
    print(f"  - Total customers: {Cliente.objects.filter(empresa=empresa_usa).count()}")
    print(f"  - Total vehicles: {Vehiculo.objects.filter(empresa=empresa_usa).count()}")
    print(f"  - Total technicians: {Tecnico.objects.filter(empresa=empresa_usa).count()}")


if __name__ == "__main__":
    crear_cuenta_usa_completa()
