#!/usr/bin/env python
"""
Script para crear repuestos de prueba para la búsqueda AJAX
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from decimal import Decimal

from django.contrib.auth.models import User

from taller.models.empresa import Empresa
from taller.models.repuesto import CategoriaRepuesto, Repuesto


def main():
    print("🔧 Creando repuestos de prueba para búsqueda AJAX")
    print("=" * 50)

    # Obtener usuario admin
    try:
        admin_user = User.objects.get(username="admin")
        print(f"✅ Usuario admin encontrado: {admin_user}")
    except User.DoesNotExist:
        print("❌ Usuario admin no encontrado")
        return

    # Obtener o crear empresa
    try:
        empresa = Empresa.objects.get(user=admin_user)
        print(f"✅ Empresa encontrada: {empresa}")
    except Empresa.DoesNotExist:
        empresa, created = Empresa.objects.get_or_create(
            user=admin_user, defaults={"nombre_taller": "Taller Admin"}
        )
        print(f"✅ Empresa {'creada' if created else 'encontrada'}: {empresa}")

    # Crear categorías
    categorias_data = ["Filtros", "Frenos", "Motor", "Suspensión", "Eléctrico"]

    categorias = {}
    for cat_name in categorias_data:
        categoria, created = CategoriaRepuesto.objects.get_or_create(
            empresa=empresa, nombre=cat_name
        )
        categorias[cat_name] = categoria
        print(f"✅ Categoría {'creada' if created else 'encontrada'}: {cat_name}")

    # Crear repuestos
    repuestos_data = [
        {
            "nombre": "Filtro de Aceite Toyota",
            "part_number": "TOY-FO-001",
            "categoria": categorias["Filtros"],
            "precio_compra": Decimal("15.50"),
            "precio_venta": Decimal("25.00"),
            "cantidad_stock": 25,
            "proveedor": "Toyota Original",
        },
        {
            "nombre": "Pastillas de Freno Delanteras",
            "part_number": "BRK-PAD-F01",
            "categoria": categorias["Frenos"],
            "precio_compra": Decimal("45.00"),
            "precio_venta": Decimal("75.00"),
            "cantidad_stock": 12,
            "proveedor": "Brembo",
        },
        {
            "nombre": "Bujías NGK Platino",
            "part_number": "NGK-SP-4x",
            "categoria": categorias["Motor"],
            "precio_compra": Decimal("8.25"),
            "precio_venta": Decimal("15.00"),
            "cantidad_stock": 48,
            "proveedor": "NGK",
        },
        {
            "nombre": "Amortiguador Delantero",
            "part_number": "SHOCK-F-001",
            "categoria": categorias["Suspensión"],
            "precio_compra": Decimal("85.00"),
            "precio_venta": Decimal("140.00"),
            "cantidad_stock": 6,
            "proveedor": "Monroe",
        },
        {
            "nombre": "Batería 12V 75Ah",
            "part_number": "BAT-12V-75",
            "categoria": categorias["Eléctrico"],
            "precio_compra": Decimal("120.00"),
            "precio_venta": Decimal("180.00"),
            "cantidad_stock": 8,
            "proveedor": "Bosch",
        },
        {
            "nombre": "Filtro de Aire Honda",
            "part_number": "HON-FA-002",
            "categoria": categorias["Filtros"],
            "precio_compra": Decimal("12.00"),
            "precio_venta": Decimal("20.00"),
            "cantidad_stock": 30,
            "proveedor": "Honda Original",
        },
    ]

    for datos in repuestos_data:
        repuesto, created = Repuesto.objects.get_or_create(
            empresa=empresa, part_number=datos["part_number"], defaults=datos
        )
        status = "✅ Creado" if created else "⚠️  Ya existe"
        print(f"{status}: {repuesto.nombre} ({repuesto.part_number})")

    total = Repuesto.objects.filter(empresa=empresa).count()
    print(f"\n📊 Total de repuestos en el sistema: {total}")
    print("🎉 ¡Repuestos de prueba listos para búsqueda AJAX!")


if __name__ == "__main__":
    main()
