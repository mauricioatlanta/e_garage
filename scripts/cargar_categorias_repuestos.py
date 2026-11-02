#!/usr/bin/env python
"""
Script para cargar categorías básicas de repuestos en el sistema.
"""

import os
import sys

import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.db import transaction

from taller.models.empresa import Empresa
from taller.models.repuesto import CategoriaRepuesto


def cargar_categorias():
    """Cargar categorías básicas de repuestos."""

    categorias_basicas = [
        "Frenos",
        "Motor",
        "Suspensión",
        "Transmisión",
        "Sistema Eléctrico",
        "Sistema de Escape",
        "Carrocería",
        "Neumáticos",
        "Filtros",
        "Aceites y Lubricantes",
        "Refrigeración",
        "Combustible",
        "Dirección",
        "Iluminación",
        "Aire Acondicionado",
        "Otros",
    ]

    # Obtener todas las empresas
    empresas = Empresa.objects.all()

    if not empresas.exists():
        print("⚠️ No hay empresas en el sistema. Primero debe crear empresas.")
        return

    for empresa in empresas:
        print(f"\n🏢 Procesando empresa: {empresa.nombre_taller}")

        with transaction.atomic():
            for categoria_nombre in categorias_basicas:
                categoria, creada = CategoriaRepuesto.objects.get_or_create(
                    empresa=empresa, nombre=categoria_nombre
                )

                if creada:
                    print(f"  ✅ Creada categoría: {categoria_nombre}")
                else:
                    print(f"  ⏭️ Ya existe categoría: {categoria_nombre}")

    print("\n🎯 Proceso completado. Categorías disponibles para todas las empresas.")


if __name__ == "__main__":
    print("🚀 Iniciando carga de categorías de repuestos...")
    cargar_categorias()
    print("✅ Proceso finalizado.")
