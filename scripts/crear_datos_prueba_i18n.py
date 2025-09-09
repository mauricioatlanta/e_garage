#!/usr/bin/env python
"""
Script para crear datos de prueba que demuestren el funcionamiento del sistema i18n
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
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.repuesto import Repuesto
from taller.models.taller_info import TallerInfo
from taller.models.vehiculos import Vehiculo


def crear_datos_prueba():
    print("🌍 Creando datos de prueba para demostrar i18n...")
    
    # 1. Crear empresa Chile (idioma español)
    print("\n📍 Creando empresa Chile...")
    empresa_chile, created = Empresa.objects.get_or_create(
        nombre="Taller Mecánico Santiago",
        defaults={
            'direccion': 'Av. Providencia 1234, Santiago',
            'telefono': '+56-2-2345-6789',
            'email': 'contacto@tallersantiago.cl',
            'pais': 'CL',
            'moneda': 'CLP'
        }
    )
    if created:
        print(f"✅ Empresa Chile creada: {empresa_chile.nombre}")
    
    # 2. Crear empresa USA (idioma inglés)
    print("\n🇺🇸 Creando empresa USA...")
    empresa_usa, created = Empresa.objects.get_or_create(
        nombre="Miami Auto Repair Shop",
        defaults={
            'direccion': '1234 Biscayne Blvd, Miami, FL 33132',
            'telefono': '+1-305-555-0123',
            'email': 'info@miamiautorepair.com',
            'pais': 'US',
            'moneda': 'USD'
        }
    )
    if created:
        print(f"✅ Empresa USA creada: {empresa_usa.nombre}")
    
    # 3. Crear usuarios para cada empresa
    print("\n👥 Creando usuarios...")
    
    # Usuario Chile
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
    
    # Usuario USA
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
    
    # 4. Crear talleres
    print("\n🔧 Creando talleres...")
    
    taller_chile, created = Taller.objects.get_or_create(
        nombre="Taller Principal Santiago",
        empresa=empresa_chile,
        defaults={
            'direccion': empresa_chile.direccion,
            'telefono': empresa_chile.telefono
        }
    )
    if created:
        print(f"✅ Taller Chile creado: {taller_chile.nombre}")
    
    taller_usa, created = Taller.objects.get_or_create(
        nombre="Main Miami Workshop",
        empresa=empresa_usa,
        defaults={
            'direccion': empresa_usa.direccion,
            'telefono': empresa_usa.telefono
        }
    )
    if created:
        print(f"✅ Taller USA creado: {taller_usa.nombre}")
    
    # 5. Crear marcas y modelos
    print("\n🚗 Creando marcas y modelos...")
    
    marca_toyota, _ = Marca.objects.get_or_create(nombre="Toyota")
    marca_ford, _ = Marca.objects.get_or_create(nombre="Ford")
    
    modelo_corolla, _ = Modelo.objects.get_or_create(
        nombre="Corolla", marca=marca_toyota
    )
    modelo_f150, _ = Modelo.objects.get_or_create(
        nombre="F-150", marca=marca_ford
    )
    
    # 6. Crear clientes
    print("\n👥 Creando clientes...")
    
    # Cliente Chile
    cliente_chile, created = Cliente.objects.get_or_create(
        rut="12345678-9",
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
        rut="US-123456789",
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
    
    # 7. Crear vehículos
    print("\n🚙 Creando vehículos...")
    
    vehiculo_chile, created = Vehiculo.objects.get_or_create(
        patente="ABCD12",
        defaults={
            'marca': marca_toyota,
            'modelo': modelo_corolla,
            'año': 2020,
            'color': 'Blanco',
            'cliente': cliente_chile
        }
    )
    if created:
        print(f"✅ Vehículo Chile creado: {vehiculo_chile.patente}")
    
    vehiculo_usa, created = Vehiculo.objects.get_or_create(
        patente="ABC123",
        defaults={
            'marca': marca_ford,
            'modelo': modelo_f150,
            'año': 2021,
            'color': 'Blue',
            'cliente': cliente_usa
        }
    )
    if created:
        print(f"✅ Vehículo USA creado: {vehiculo_usa.patente}")
    
    # 8. Crear servicios
    print("\n🛠️ Creando servicios...")
    
    # Servicios para Chile (en español)
    servicio_chile, created = Servicio.objects.get_or_create(
        nombre="Cambio de aceite y filtros",
        defaults={
            'descripcion': 'Cambio de aceite motor, filtro de aceite y filtro de aire',
            'precio': Decimal('35000'),
            'tiempo_estimado': 60,
            'empresa': empresa_chile
        }
    )
    if created:
        print(f"✅ Servicio Chile creado: {servicio_chile.nombre}")
    
    # Servicios para USA (en inglés)
    servicio_usa, created = Servicio.objects.get_or_create(
        nombre="Oil Change and Filter Service",
        defaults={
            'descripcion': 'Engine oil change, oil filter and air filter replacement',
            'precio': Decimal('89.99'),
            'tiempo_estimado': 60,
            'empresa': empresa_usa
        }
    )
    if created:
        print(f"✅ Servicio USA creado: {servicio_usa.nombre}")
    
    # 9. Crear repuestos
    print("\n🔧 Creando repuestos...")
    
    # Repuesto Chile
    repuesto_chile, created = Repuesto.objects.get_or_create(
        codigo="FIL-001-CL",
        defaults={
            'nombre': 'Filtro de aceite Toyota',
            'descripcion': 'Filtro de aceite original Toyota para Corolla',
            'precio': Decimal('8500'),
            'stock': 25,
            'empresa': empresa_chile
        }
    )
    if created:
        print(f"✅ Repuesto Chile creado: {repuesto_chile.nombre}")
    
    # Repuesto USA
    repuesto_usa, created = Repuesto.objects.get_or_create(
        codigo="FIL-001-US",
        defaults={
            'nombre': 'Ford Oil Filter',
            'descripcion': 'Original Ford oil filter for F-150',
            'precio': Decimal('24.99'),
            'stock': 30,
            'empresa': empresa_usa
        }
    )
    if created:
        print(f"✅ Repuesto USA creado: {repuesto_usa.nombre}")
    
    # 10. Crear documentos de ejemplo
    print("\n📄 Creando documentos de ejemplo...")
    
    # Documento Chile (Presupuesto)
    doc_chile, created = Documento.objects.get_or_create(
        numero="P-2024-001",
        defaults={
            'tipo': 'presupuesto',
            'fecha': datetime.now().date(),
            'cliente': cliente_chile,
            'vehiculo': vehiculo_chile,
            'taller': taller_chile,
            'usuario': user_chile,
            'observaciones': 'Presupuesto para mantenimiento preventivo',
            'descuento': Decimal('0'),
            'impuesto': Decimal('19'),  # IVA Chile
            'estado': 'borrador'
        }
    )
    if created:
        print(f"✅ Documento Chile creado: {doc_chile.numero}")
        
        # Agregar detalles al documento Chile
        DetalleDocumento.objects.create(
            documento=doc_chile,
            tipo='servicio',
            servicio=servicio_chile,
            descripcion=servicio_chile.nombre,
            cantidad=1,
            precio_unitario=servicio_chile.precio,
            descuento=Decimal('0')
        )
        
        DetalleDocumento.objects.create(
            documento=doc_chile,
            tipo='repuesto',
            repuesto=repuesto_chile,
            descripcion=repuesto_chile.nombre,
            cantidad=1,
            precio_unitario=repuesto_chile.precio,
            descuento=Decimal('0')
        )
    
    # Documento USA (Quote)
    doc_usa, created = Documento.objects.get_or_create(
        numero="Q-2024-001",
        defaults={
            'tipo': 'presupuesto',
            'fecha': datetime.now().date(),
            'cliente': cliente_usa,
            'vehiculo': vehiculo_usa,
            'taller': taller_usa,
            'usuario': user_usa,
            'observaciones': 'Quote for preventive maintenance service',
            'descuento': Decimal('0'),
            'impuesto': Decimal('8.25'),  # Sales tax Florida
            'estado': 'borrador'
        }
    )
    if created:
        print(f"✅ Documento USA creado: {doc_usa.numero}")
        
        # Agregar detalles al documento USA
        DetalleDocumento.objects.create(
            documento=doc_usa,
            tipo='servicio',
            servicio=servicio_usa,
            descripcion=servicio_usa.nombre,
            cantidad=1,
            precio_unitario=servicio_usa.precio,
            descuento=Decimal('0')
        )
        
        DetalleDocumento.objects.create(
            documento=doc_usa,
            tipo='repuesto',
            repuesto=repuesto_usa,
            descripcion=repuesto_usa.nombre,
            cantidad=1,
            precio_unitario=repuesto_usa.precio,
            descuento=Decimal('0')
        )
    
    print("\n🎉 ¡Datos de prueba creados exitosamente!")
    print("\n📋 Resumen de datos creados:")
    print(f"   🏢 Empresas: {Empresa.objects.count()}")
    print(f"   🔧 Talleres: {Taller.objects.count()}")
    print(f"   👥 Usuarios: {User.objects.count()}")
    print(f"   👤 Clientes: {Cliente.objects.count()}")
    print(f"   🚗 Vehículos: {Vehiculo.objects.count()}")
    print(f"   🛠️ Servicios: {Servicio.objects.count()}")
    print(f"   🔧 Repuestos: {Repuesto.objects.count()}")
    print(f"   📄 Documentos: {Documento.objects.count()}")
    
    print("\n🔑 Credenciales de acceso:")
    print(f"   Chile: admin_chile / admin123")
    print(f"   USA:   admin_usa / admin123")
    
    print("\n💡 Para probar el sistema i18n:")
    print("   1. Inicia sesión con admin_chile para ver la interfaz en español")
    print("   2. Inicia sesión con admin_usa para ver la interfaz en inglés")
    print("   3. También puedes cambiar idioma manualmente usando el selector")

if __name__ == "__main__":
    crear_datos_prueba()
