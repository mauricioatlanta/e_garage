#!/usr/bin/env python
"""
Script para crear datos de prueba que aseguren que el listado de documentos
muestre conteos correctos en MILLAS, #REP, #SERV, #OTROS
"""

import os
import sys
from decimal import Decimal

import django

# Setup Django
sys.path.append(".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.models import (
    Cliente,
    Documento,
    Empresa,
    LineaOtroServicio,
    LineaRepuesto,
    LineaServicio,
    OtroServicio,
    Repuesto,
    TipoServicio,
    Vehiculo,
)
from taller.models.marca import Marca
from taller.models.modelo import Modelo


def crear_datos_prueba():
    print("🔧 Creando datos de prueba para documentos...")

    # 1. Crear usuario y empresa si no existe
    user, created = User.objects.get_or_create(
        username="admin_test", defaults={"email": "admin@test.com", "is_staff": True}
    )
    if created:
        user.set_password("admin123")
        user.save()
        print(f"✅ Usuario creado: {user.username}")

    empresa, created = Empresa.objects.get_or_create(
        user=user,
        defaults={"nombre_taller": "Taller Demo", "pais": "CL", "currency": "CLP"},
    )
    if created:
        print(f"✅ Empresa creada: {empresa.nombre_taller}")

    # 2. Crear cliente
    cliente, created = Cliente.objects.get_or_create(
        empresa=empresa,
        rut="12345678-9",
        defaults={
            "nombre": "Cliente Demo",
            "email": "cliente@demo.com",
            "telefono": "+56912345678",
        },
    )
    if created:
        print(f"✅ Cliente creado: {cliente.nombre}")

    # 3. Crear marca y modelo
    marca, created = Marca.objects.get_or_create(
        empresa=empresa, nombre="Toyota", defaults={"pais": "CL"}
    )
    if created:
        print(f"✅ Marca creada: {marca.nombre}")

    modelo, created = Modelo.objects.get_or_create(
        empresa=empresa,
        marca=marca,
        nombre="Corolla",
        defaults={"anio_inicio": 2020, "anio_fin": 2024},
    )
    if created:
        print(f"✅ Modelo creado: {modelo.nombre}")

    # 4. Crear vehículo
    vehiculo, created = Vehiculo.objects.get_or_create(
        empresa=empresa,
        cliente=cliente,
        patente="ABC123",
        defaults={"marca": marca, "modelo": modelo, "anio": 2022},
    )
    if created:
        print(f"✅ Vehículo creado: {vehiculo.patente}")

    # 5. Crear repuestos de prueba
    repuesto1, created = Repuesto.objects.get_or_create(
        empresa=empresa,
        codigo="REP001",
        defaults={
            "nombre": "Filtro de Aceite",
            "precio": Decimal("15000"),
            "stock": 100,
        },
    )

    repuesto2, created = Repuesto.objects.get_or_create(
        empresa=empresa,
        codigo="REP002",
        defaults={
            "nombre": "Pastillas de Freno",
            "precio": Decimal("45000"),
            "stock": 50,
        },
    )

    # 6. Crear tipos de servicio
    servicio1, created = TipoServicio.objects.get_or_create(
        empresa=empresa,
        nombre="Cambio de Aceite",
        defaults={"precio_base": Decimal("25000"), "categoria": "MANTENIMIENTO"},
    )

    servicio2, created = TipoServicio.objects.get_or_create(
        empresa=empresa,
        nombre="Revisión de Frenos",
        defaults={"precio_base": Decimal("35000"), "categoria": "MANTENIMIENTO"},
    )

    # 7. Crear otros servicios
    otro_servicio, created = OtroServicio.objects.get_or_create(
        empresa=empresa,
        nombre="Limpieza del Vehículo",
        defaults={"precio_cliente": Decimal("15000"), "categoria": "ADICIONAL"},
    )

    # 8. Crear documento con líneas
    documento, created = Documento.objects.get_or_create(
        empresa=empresa,
        cliente=cliente,
        vehiculo=vehiculo,
        tipo="OT",
        numero=1001,
        defaults={"estado": "DRAFT", "moneda": "CLP", "country": "CL"},
    )

    if created:
        print(f"✅ Documento creado: {documento.numero_documento}")

        # Crear líneas de repuestos
        LineaRepuesto.objects.create(
            documento=documento,
            repuesto=repuesto1,
            cantidad=2,
            precio_unitario=repuesto1.precio,
            descuento=0,
        )

        LineaRepuesto.objects.create(
            documento=documento,
            repuesto=repuesto2,
            cantidad=1,
            precio_unitario=repuesto2.precio,
            descuento=10,  # 10% descuento
        )

        print("✅ Líneas de repuesto creadas")

        # Crear líneas de servicios
        LineaServicio.objects.create(
            documento=documento,
            servicio=servicio1,
            cantidad=1,
            precio_unitario=servicio1.precio_base,
            descuento=0,
        )

        LineaServicio.objects.create(
            documento=documento,
            servicio=servicio2,
            cantidad=1,
            precio_unitario=servicio2.precio_base,
            descuento=0,
        )

        print("✅ Líneas de servicio creadas")

        # Crear línea de otro servicio
        LineaOtroServicio.objects.create(
            documento=documento,
            servicio=otro_servicio,
            cantidad=1,
            precio_cliente=otro_servicio.precio_cliente,
        )

        print("✅ Línea de otro servicio creada")

    # 9. Crear documento adicional para tener más datos
    documento2, created = Documento.objects.get_or_create(
        empresa=empresa,
        cliente=cliente,
        vehiculo=vehiculo,
        tipo="PRES",
        numero=2001,
        defaults={"estado": "DRAFT", "moneda": "CLP", "country": "CL"},
    )

    if created:
        print(f"✅ Documento 2 creado: {documento2.numero_documento}")

        # Solo repuestos en este documento
        LineaRepuesto.objects.create(
            documento=documento2,
            repuesto=repuesto1,
            cantidad=1,
            precio_unitario=repuesto1.precio,
            descuento=0,
        )

        # Solo servicios en este documento
        LineaServicio.objects.create(
            documento=documento2,
            servicio=servicio1,
            cantidad=2,
            precio_unitario=servicio1.precio_base,
            descuento=5,
        )

        print("✅ Líneas para documento 2 creadas")

    # 10. Verificar los datos creados
    print("\n📊 RESUMEN DE DATOS CREADOS:")
    print(f"Total documentos: {Documento.objects.count()}")
    print(f"Total líneas repuesto: {LineaRepuesto.objects.count()}")
    print(f"Total líneas servicio: {LineaServicio.objects.count()}")
    print(f"Total líneas otros: {LineaOtroServicio.objects.count()}")

    print("\n📋 CONTEOS POR DOCUMENTO:")
    for doc in Documento.objects.all():
        rep_count = doc.lineas_repuesto.count()
        serv_count = doc.lineas_servicio.count()
        otros_count = doc.lineas_otro_servicio.count()
        print(
            f"Doc {doc.numero_documento}: {rep_count} rep, {serv_count} serv, {otros_count} otros"
        )

    print("\n✅ Datos de prueba creados exitosamente!")
    print("🌐 Ahora puedes probar:")
    print("   - Lista debug: http://127.0.0.1:8000/documentos/lista-debug/")
    print("   - Lista principal: http://127.0.0.1:8000/cl/documentos/cl/")


if __name__ == "__main__":
    crear_datos_prueba()
