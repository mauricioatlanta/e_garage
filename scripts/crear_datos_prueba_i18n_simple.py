#!/usr/bin/env python
"""
Script simplificado para crear datos de prueba que demuestren el funcionamiento del sistema i18n
"""
import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import translation

from taller.models.clientes import Cliente
from taller.models.empresa import Empresa
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.vehiculos import Vehiculo


def crear_datos_prueba():
    print("🌍 Creando datos de prueba para demostrar i18n...")
    
    # 1. Crear usuario y empresa Chile (idioma español)
    print("\n📍 Creando usuario y empresa Chile...")
    user_chile, created = User.objects.get_or_create(
        username="admin_chile",
        defaults={
            'first_name': 'Carlos',
            'last_name': 'González',
            'email': 'carlos@tallersantiago.cl',
            'is_active': True,
            'is_staff': True
        }
    )
    if created:
        user_chile.set_password('admin123')
        user_chile.save()
        print(f"✅ Usuario Chile creado: {user_chile.username}")
    
    # Crear empresa asociada al usuario Chile
    empresa_chile, created = Empresa.objects.get_or_create(
        user=user_chile,
        defaults={
            'nombre_taller': "Taller Mecánico Santiago",
            'empresa': "Servicios Automotrices Chile Ltda.",
            'pais': 'CL',
            'direccion': 'Av. Providencia 1234, Santiago',
            'telefono': '+56-2-2345-6789'
        }
    )
    if created:
        print(f"✅ Empresa Chile creada: {empresa_chile.nombre_taller}")
    
    # 2. Crear usuario y empresa USA (idioma inglés)
    print("\n🇺🇸 Creando usuario y empresa USA...")
    user_usa, created = User.objects.get_or_create(
        username="admin_usa",
        defaults={
            'first_name': 'John',
            'last_name': 'Smith',
            'email': 'john@miamiautorepair.com',
            'is_active': True,
            'is_staff': True
        }
    )
    if created:
        user_usa.set_password('admin123')
        user_usa.save()
        print(f"✅ Usuario USA creado: {user_usa.username}")
    
    # Crear empresa asociada al usuario USA
    empresa_usa, created = Empresa.objects.get_or_create(
        user=user_usa,
        defaults={
            'nombre_taller': "Miami Auto Repair Shop",
            'empresa': "Miami Automotive Services LLC",
            'pais': 'US',
            'direccion': '1234 Biscayne Blvd, Miami, FL 33132',
            'telefono': '+1-305-555-0123'
        }
    )
    if created:
        print(f"✅ Empresa USA creada: {empresa_usa.nombre_taller}")
    
    # 3. Crear marcas y modelos
    print("\n🚗 Creando marcas y modelos...")
    
    marca_toyota, _ = Marca.objects.get_or_create(nombre="Toyota")
    marca_ford, _ = Marca.objects.get_or_create(nombre="Ford")
    
    modelo_corolla, _ = Modelo.objects.get_or_create(
        nombre="Corolla", marca=marca_toyota
    )
    modelo_f150, _ = Modelo.objects.get_or_create(
        nombre="F-150", marca=marca_ford
    )
    
    # 4. Crear clientes
    print("\n👥 Creando clientes...")
    
    # Cliente Chile
    cliente_chile, created = Cliente.objects.get_or_create(
        tax_id="12345678-9",
        defaults={
            'nombre': 'María',
            'apellido': 'Rodríguez',
            'telefono': '+56-9-8765-4321',
            'email': 'maria.rodriguez@email.cl',
            'direccion': 'Las Condes 567, Santiago',
            'empresa': empresa_chile
        }
    )
    if created:
        print(f"✅ Cliente Chile creado: {cliente_chile.nombre} {cliente_chile.apellido}")
    
    # Cliente USA
    cliente_usa, created = Cliente.objects.get_or_create(
        tax_id="US-123456789",
        defaults={
            'nombre': 'Sarah',
            'apellido': 'Johnson',
            'telefono': '+1-305-555-9876',
            'email': 'sarah.johnson@email.com',
            'direccion': '789 Ocean Drive, Miami Beach, FL',
            'empresa': empresa_usa
        }
    )
    if created:
        print(f"✅ Cliente USA creado: {cliente_usa.nombre} {cliente_usa.apellido}")
    
    # 5. Crear vehículos
    print("\n🚙 Creando vehículos...")
    
    vehiculo_chile, created = Vehiculo.objects.get_or_create(
        patente="ABCD12",
        defaults={
            'marca': marca_toyota,
            'modelo': modelo_corolla,
            'anio': 2020,
            'cliente': cliente_chile,
            'empresa': empresa_chile
        }
    )
    if created:
        print(f"✅ Vehículo Chile creado: {vehiculo_chile.patente}")
    
    vehiculo_usa, created = Vehiculo.objects.get_or_create(
        patente="ABC123",
        defaults={
            'marca': marca_ford,
            'modelo': modelo_f150,
            'anio': 2021,
            'cliente': cliente_usa,
            'empresa': empresa_usa
        }
    )
    if created:
        print(f"✅ Vehículo USA creado: {vehiculo_usa.patente}")
    
    print("\n🎉 ¡Datos de prueba creados exitosamente!")
    print("\n📋 Resumen de datos creados:")
    print(f"   🏢 Empresas: {Empresa.objects.count()}")
    print(f"   👥 Usuarios: {User.objects.count()}")
    print(f"   👤 Clientes: {Cliente.objects.count()}")
    print(f"   🚗 Vehículos: {Vehiculo.objects.count()}")
    print(f"   🏷️ Marcas: {Marca.objects.count()}")
    print(f"   🚙 Modelos: {Modelo.objects.count()}")
    
    print("\n🔑 Credenciales de acceso:")
    print(f"   Chile: admin_chile / admin123")
    print(f"   USA:   admin_usa / admin123")
    
    print("\n💡 Para probar el sistema i18n:")
    print("   1. Inicia sesión con admin_chile para ver la interfaz en español")
    print("   2. Inicia sesión con admin_usa para ver la interfaz en inglés")
    print("   3. También puedes cambiar idioma manualmente usando el selector")
    print("\n🌍 El sistema detectará automáticamente el idioma según el país de la empresa:")
    print("   - Empresas con país 'CL' → Español")
    print("   - Empresas con país 'US' → English")

if __name__ == "__main__":
    crear_datos_prueba()
