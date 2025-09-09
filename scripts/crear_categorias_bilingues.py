#!/usr/bin/env python
"""
Script para crear categorías de repuestos bilingües
Crea categorías en inglés y español para ambos países
"""

import os
import sys

import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.empresa import Empresa
from taller.models.repuesto import CategoriaRepuesto


def crear_categorias_bilingues():
    """Crea categorías de repuestos en inglés y español"""
    
    print("🔧 Creando categorías de repuestos bilingües...")
    
    # Categorías en español
    categorias_espanol = [
        'Motor',
        'Frenos', 
        'Sistema Eléctrico',
        'Suspensión',
        'Transmisión',
        'Sistema de Escape',
        'Refrigeración',
        'Combustible',
        'Carrocería',
        'Neumáticos',
        'Filtros',
        'Aceites y Lubricantes'
    ]
    
    # Categorías en inglés
    categorias_ingles = [
        'Engine',
        'Brake',
        'Electrical', 
        'Suspension',
        'Transmission',
        'Exhaust',
        'Cooling',
        'Fuel',
        'Body',
        'Tires',
        'Filters',
        'Oils'
    ]
    
    # Obtener todas las empresas
    empresas = Empresa.objects.all()
    
    for empresa in empresas:
        print(f"📋 Procesando empresa: {empresa.nombre_taller} ({empresa.pais})")
        
        # Determinar qué categorías crear según el país
        if empresa.pais == 'US':
            categorias_a_crear = categorias_ingles
        else:
            categorias_a_crear = categorias_espanol
        
        # Crear categorías para esta empresa
        for nombre_categoria in categorias_a_crear:
            categoria, created = CategoriaRepuesto.objects.get_or_create(
                empresa=empresa,
                nombre=nombre_categoria,
                defaults={}
            )
            
            if created:
                print(f"  ✅ Creada: {nombre_categoria}")
            else:
                print(f"  ⚠️ Ya existe: {nombre_categoria}")
    
    print("🎉 Categorías bilingües creadas exitosamente!")

if __name__ == "__main__":
    crear_categorias_bilingues()
